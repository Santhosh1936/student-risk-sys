import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db
from ..services.dependencies import require_student
from ..models.models import User, Student, SemesterRecord, SubjectGrade, AttendanceRecord
from ..services.grade_extractor import extract_from_file, get_gemini_status
from ..services.risk_engine import compute_risk_score, get_student_risk, compute_cgpa
from ..services.advisor import send_message as advisor_send, get_chat_history as advisor_history, mark_data_updated

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/student", tags=["Student"])

# ── Student dependency helper ─────────────────────────────────────────────────

def get_student_or_404(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
) -> Student:
    s = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "Student profile not found.")
    return s

# Per-student chat rate limit
_chat_attempts: dict = defaultdict(list)
_CHAT_MAX = 10
_CHAT_WINDOW = 60

def _check_chat_rate(student_id: int):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=_CHAT_WINDOW)
    _chat_attempts[student_id] = [
        t for t in _chat_attempts[student_id] if t > cutoff
    ]
    if len(_chat_attempts[student_id]) >= _CHAT_MAX:
        raise HTTPException(
            429,
            "Chat rate limit reached. Please wait a minute before sending more messages.",
        )
    _chat_attempts[student_id].append(now)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class StudentProfileResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    roll_number: Optional[str] = None
    branch: Optional[str] = None
    enrollment_year: Optional[int] = None
    current_semester: int
    cgpa: Optional[float] = None

    class Config:
        from_attributes = True


class SubjectInput(BaseModel):
    sno: int
    subject_code: str
    subject_name: str
    grade_letter: str
    grade_points: int
    credits: float
    is_backlog: bool
    result: str = "P"


class AdvisorChatRequest(BaseModel):
    message: str


class ConfirmUploadRequest(BaseModel):
    hall_ticket_no: Optional[str] = None
    serial_no: Optional[str] = None
    student_name: Optional[str] = None
    branch: Optional[str] = None
    examination: Optional[str] = None
    semester_no: int
    exam_month_year: Optional[str] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    total_credits_this_semester: Optional[float] = None
    cumulative_credits: Optional[float] = None
    subjects: List[SubjectInput]


class AttendanceSubjectInput(BaseModel):
    subject_name: str
    classes_attended: int
    total_classes: int


class SubmitAttendanceRequest(BaseModel):
    semester_no: int
    subjects: List[AttendanceSubjectInput]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/extraction-status")
def extraction_status(
    current_user: User = Depends(require_student)
):
    """Returns Gemini API configuration status."""
    return get_gemini_status()


@router.get("/profile", response_model=StudentProfileResponse)
def get_student_profile(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    s = db.query(Student).filter(Student.user_id == current_user.id).first()

    # Recompute CGPA from semester records if profile value is stale or missing
    if s:
        computed_cgpa = compute_cgpa(s.id, db)
        if computed_cgpa is not None and s.cgpa != computed_cgpa:
            s.cgpa = computed_cgpa
            db.commit()

    return StudentProfileResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        roll_number=current_user.roll_number,
        branch=s.branch if s else None,
        enrollment_year=s.enrollment_year if s else None,
        current_semester=s.current_semester if s else 1,
        cgpa=s.cgpa if s else None,
    )


@router.post("/extract-marksheet")
async def extract_marksheet(
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    STEP 1 of 2: Upload file -> extract with Claude Vision -> return for review.
    Data is NOT saved to database yet.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{ext}' not allowed. Use PDF, JPG, or PNG.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Maximum size is 10MB.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        parsed = extract_from_file(file_path)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Extraction failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return {
        "status": "extracted",
        "message": "Review the extracted data and correct any errors before saving.",
        "extracted": parsed
    }


@router.post("/confirm-marksheet", status_code=201)
def confirm_marksheet(
    data: ConfirmUploadRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    STEP 2 of 2: Save confirmed (possibly edited) data to database.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    # Block duplicate semester
    existing = db.query(SemesterRecord).filter(
        SemesterRecord.student_id == student.id,
        SemesterRecord.semester_no == data.semester_no
    ).first()
    if existing:
        raise HTTPException(
            409,
            f"Semester {data.semester_no} already saved. "
            "Delete it first if you want to re-upload."
        )

    # Save SemesterRecord
    record = SemesterRecord(
        student_id=student.id,
        semester_no=data.semester_no,
        gpa=data.sgpa,
        credits_attempted=sum(s.credits for s in data.subjects),
        credits_earned=(
            data.total_credits_this_semester
            if data.total_credits_this_semester is not None
            else sum(s.credits for s in data.subjects if not s.is_backlog)
        ),
        is_confirmed=True
    )
    db.add(record)
    db.flush()

    # BL-08: Validate grade_letter before saving
    VALID_GRADES = {
        "O", "A+", "A", "B+", "B", "C", "D", "F",
        "AB", "S*", "NS", "NS*", "P"
    }
    for s in data.subjects:
        if s.grade_letter and \
           s.grade_letter.upper() not in VALID_GRADES:
            raise HTTPException(
                422,
                f"Invalid grade '{s.grade_letter}' for "
                f"'{s.subject_name}'. Valid: "
                f"{', '.join(sorted(VALID_GRADES))}"
            )

    # Validate grade_points and credits before saving
    for subj in data.subjects:
        if subj.grade_points is not None and not (0 <= subj.grade_points <= 10):
            raise HTTPException(
                400,
                f"Invalid grade_points {subj.grade_points} for '{subj.subject_name}'. Must be 0-10."
            )
        if subj.credits is not None and not (0 <= subj.credits <= 6):
            raise HTTPException(
                400,
                f"Invalid credits {subj.credits} for '{subj.subject_name}'. Must be 0-6."
            )

    # Save SubjectGrades
    for subj in data.subjects:
        db.add(SubjectGrade(
            semester_record_id=record.id,
            subject_name=subj.subject_name,
            subject_code=subj.subject_code,
            grade_letter=subj.grade_letter,
            grade_points=subj.grade_points,
            credits=subj.credits,
            is_backlog=subj.is_backlog,
        ))

    # Update student profile
    if data.branch and not student.branch:
        student.branch = data.branch
    if data.semester_no >= (student.current_semester or 1):
        student.current_semester = data.semester_no

    # Recalculate CGPA using correct JNTUH credits-weighted formula.
    # compute_cgpa sees the new SemesterRecord because of the db.flush() above.
    correct_cgpa = compute_cgpa(student.id, db)
    if correct_cgpa is not None:
        student.cgpa = correct_cgpa

    db.commit()

    # Auto-compute risk score after grade confirmation
    try:
        from ..services.risk_engine import compute_risk_score
        compute_risk_score(student.id, db)
    except Exception as e:
        logger.warning(f"Auto risk computation failed: {e}")
        # Do not block the confirm response if risk fails

    # Mark chat thread for data refresh after new semester upload
    try:
        mark_data_updated(student.id, db)
    except Exception as e:
        logger.warning(f"Chat refresh flag failed: {e}")

    # Best-effort RAG refresh after marksheet confirmation
    try:
        from ..services.rag_service import index_student
        index_student(student.id, db)
    except Exception as e:
        logger.warning(f"RAG index failed: {e}")

    return {
        "message": f"Semester {data.semester_no} saved successfully.",
        "semester_record_id": record.id,
        "semester_no": data.semester_no,
        "subjects_saved": len(data.subjects)
    }


@router.get("/semesters")
def get_student_semesters(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return []

    records = (
        db.query(SemesterRecord)
        .options(joinedload(SemesterRecord.subjects))
        .filter(SemesterRecord.student_id == student.id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )

    result = []
    for r in records:
        subjects = r.subjects
        result.append({
            "semester_no": r.semester_no,
            "semester_record_id": r.id,
            "gpa": r.gpa,
            "credits_earned": r.credits_earned,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            "subjects": [{
                "subject_code": s.subject_code,
                "subject_name": s.subject_name,
                "grade_letter": s.grade_letter,
                "grade_points": s.grade_points,
                "credits": s.credits,
                "is_backlog": s.is_backlog,
            } for s in subjects]
        })
    return result


@router.post("/compute-risk")
def trigger_risk_computation(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Manually trigger SARS risk score computation for the logged-in student.
    Also called automatically after every confirmed grade upload.
    """
    student = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    try:
        breakdown = compute_risk_score(student.id, db)
    except Exception as e:
        raise HTTPException(500, f"Risk computation failed: {e}")

    return {
        "message": "Risk score computed successfully.",
        "sars_score": breakdown["sars_score"],
        "risk_level": breakdown["risk_level"],
        "confidence": breakdown["confidence"],
        "factor_breakdown": breakdown,
    }


@router.get("/risk-score")
def get_risk_score(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Return the latest stored SARS risk score for the logged-in student.
    Returns 404 with message if not yet computed.
    """
    student = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    risk = get_student_risk(student.id, db)
    if not risk:
        return {
            "computed": False,
            "message": "Risk score not yet computed. "
                       "Upload a semester marksheet to compute it.",
            "sars_score": None,
            "risk_level": None,
        }

    return {"computed": True, **risk}


@router.delete("/semesters/{semester_no}")
def delete_semester(
    semester_no: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(404, "Student not found.")

    record = db.query(SemesterRecord).filter(
        SemesterRecord.student_id == student.id,
        SemesterRecord.semester_no == semester_no
    ).first()
    if not record:
        raise HTTPException(404, f"Semester {semester_no} not found.")

    db.query(SubjectGrade).filter(
        SubjectGrade.semester_record_id == record.id
    ).delete()
    db.delete(record)
    db.commit()

    # Recompute CGPA after semester deletion
    correct_cgpa = compute_cgpa(student.id, db)
    if correct_cgpa is not None:
        student.cgpa = correct_cgpa
    else:
        student.cgpa = None
    db.commit()

    # Recompute risk score with updated data
    try:
        compute_risk_score(student.id, db)
    except Exception as e:
        logger.warning(f"Risk recompute after delete failed: {e}")

    # Mark advisor context stale after semester deletion
    try:
        mark_data_updated(student.id, db)
    except Exception as e:
        logger.warning(f"Chat refresh flag failed after semester delete: {e}")

    # Best-effort RAG refresh after semester deletion
    try:
        from ..services.rag_service import index_student
        index_student(student.id, db)
    except Exception as e:
        logger.warning(f"RAG index failed after semester delete: {e}")

    # Update current_semester to reflect remaining records
    remaining = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student.id)
        .order_by(SemesterRecord.semester_no.desc())
        .first()
    )
    student.current_semester = (remaining.semester_no + 1) if remaining else 1
    db.commit()

    return {"message": f"Semester {semester_no} deleted."}


@router.post("/attendance", status_code=201)
def submit_attendance(
    data: SubmitAttendanceRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Submit attendance for one semester (replaces existing records for that semester).
    Calculates percentage per subject automatically.
    Triggers risk score recomputation after save.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    if not data.subjects:
        raise HTTPException(400, "At least one subject is required.")

    for subj in data.subjects:
        if subj.total_classes <= 0:
            raise HTTPException(
                400,
                f"total_classes must be > 0 for subject '{subj.subject_name}'."
            )
        if subj.classes_attended < 0:
            raise HTTPException(
                400,
                f"classes_attended cannot be negative for subject '{subj.subject_name}'."
            )
        if subj.classes_attended > subj.total_classes:
            raise HTTPException(
                400,
                f"classes_attended cannot exceed total_classes for '{subj.subject_name}'."
            )

    # Delete existing attendance records for this semester
    db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        AttendanceRecord.semester_no == data.semester_no
    ).delete()

    # Insert new records
    for subj in data.subjects:
        pct = round(subj.classes_attended / subj.total_classes * 100.0, 2)
        db.add(AttendanceRecord(
            student_id=student.id,
            semester_no=data.semester_no,
            subject_name=subj.subject_name.strip(),
            classes_attended=subj.classes_attended,
            total_classes=subj.total_classes,
            percentage=pct,
        ))

    db.commit()

    # Recompute risk score with updated attendance
    try:
        compute_risk_score(student.id, db)
    except Exception as e:
        logger.warning(f"Risk recompute after attendance update failed: {e}")

    # Mark advisor context stale after attendance update
    try:
        mark_data_updated(student.id, db)
    except Exception as e:
        logger.warning(f"Chat refresh flag failed after attendance update: {e}")

    # Best-effort RAG refresh after attendance update
    try:
        from ..services.rag_service import index_student
        index_student(student.id, db)
    except Exception as e:
        logger.warning(f"RAG index failed: {e}")

    return {
        "message": f"Attendance for semester {data.semester_no} saved.",
        "semester_no": data.semester_no,
        "subjects_saved": len(data.subjects),
    }


@router.get("/attendance")
def get_attendance(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Return all attendance records for the logged-in student, grouped by semester.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return []

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student.id)
        .order_by(AttendanceRecord.semester_no, AttendanceRecord.subject_name)
        .all()
    )

    # Group by semester
    grouped: dict = {}
    for rec in records:
        sem = rec.semester_no
        if sem not in grouped:
            grouped[sem] = []
        grouped[sem].append({
            "subject_name": rec.subject_name,
            "classes_attended": rec.classes_attended,
            "total_classes": rec.total_classes,
            "percentage": rec.percentage,
        })

    return [
        {"semester_no": sem, "subjects": subjs}
        for sem, subjs in sorted(grouped.items())
    ]


@router.delete("/attendance/{semester_no}")
def delete_attendance(
    semester_no: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Delete all attendance records for a given semester.
    Triggers risk score recomputation (attendance will revert to default penalty).
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(404, "Student not found.")

    deleted = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        AttendanceRecord.semester_no == semester_no
    ).delete()

    if deleted == 0:
        raise HTTPException(404, f"No attendance records found for semester {semester_no}.")

    db.commit()

    # Recompute risk score with attendance removed
    try:
        compute_risk_score(student.id, db)
    except Exception as e:
        logger.warning(f"Risk recompute after attendance delete failed: {e}")

    # Mark advisor context stale after attendance deletion
    try:
        mark_data_updated(student.id, db)
    except Exception as e:
        logger.warning(f"Chat refresh flag failed after attendance delete: {e}")

    # Best-effort RAG refresh after attendance deletion
    try:
        from ..services.rag_service import index_student
        index_student(student.id, db)
    except Exception as e:
        logger.warning(f"RAG index failed after attendance delete: {e}")

    return {"message": f"Attendance for semester {semester_no} deleted."}


@router.post("/advisor/chat")
def advisor_chat(
    request: AdvisorChatRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI advisor. Returns AI response.
    Each student has their own isolated conversation thread.
    Context is injected automatically on first message.
    Data refresh is injected automatically after new semester upload.
    """
    student = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    _check_chat_rate(student.id)

    if not request.message or not request.message.strip():
        raise HTTPException(400, "Message cannot be empty.")

    try:
        result = advisor_send(
            student_id=student.id,
            user_message=request.message.strip(),
            db=db
        )
    except ValueError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"Advisor error: {e}")

    return result


@router.get("/advisor/history")
def advisor_get_history(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Return full chat history for the logged-in student.
    Returns only normal messages — context seeds and data
    refresh messages are hidden from the UI.
    """
    student = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    history = advisor_history(student.id, db)
    return {"messages": history, "count": len(history)}


@router.get("/rag-status")
def rag_status(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(404, "Student profile not found.")

    try:
        from ..services.rag_service import get_rag_status
        return get_rag_status(student.id)
    except Exception as e:
        logger.warning(f"RAG status failed: {e}")
        return {
            "indexed": False,
            "chunk_count": 0,
            "chunk_types": [],
        }


# ── BA-07: Update student profile ────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    roll_number: Optional[str] = None
    branch: Optional[str] = None


@router.patch("/profile")
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(404, "Profile not found.")
    if request.full_name is not None:
        current_user.full_name = request.full_name.strip()
    if request.roll_number is not None:
        current_user.roll_number = request.roll_number.strip()
    if request.branch is not None:
        student.branch = request.branch.strip()
    db.commit()

    try:
        mark_data_updated(student.id, db)
    except Exception as e:
        logger.warning(f"Chat refresh flag failed after profile update: {e}")

    try:
        from ..services.rag_service import index_student
        index_student(student.id, db)
    except Exception as e:
        logger.warning(f"RAG index failed after profile update: {e}")

    return {"message": "Profile updated successfully."}
