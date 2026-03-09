import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db
from ..services.dependencies import require_student
from ..models.models import User, Student, SemesterRecord, SubjectGrade
from ..services.grade_extractor import extract_from_file, get_gemini_status
from ..services.risk_engine import compute_risk_score, get_student_risk
from ..services.advisor import send_message as advisor_send, get_chat_history as advisor_history, mark_data_updated

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/student", tags=["Student"])

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


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/extraction-status")
def extraction_status():
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
        records = db.query(SemesterRecord).filter(
            SemesterRecord.student_id == s.id
        ).all()
        valid_gpas = [float(r.gpa) for r in records if r.gpa is not None]
        if valid_gpas:
            computed_cgpa = round(sum(valid_gpas) / len(valid_gpas), 2)
            if s.cgpa != computed_cgpa:
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


@router.post("/confirm-marksheet")
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
    if data.cgpa is not None:
        student.cgpa = data.cgpa
    if data.branch and not student.branch:
        student.branch = data.branch
    if data.semester_no >= (student.current_semester or 1):
        student.current_semester = data.semester_no

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

    records = db.query(SemesterRecord)\
        .filter(SemesterRecord.student_id == student.id)\
        .order_by(SemesterRecord.semester_no).all()

    result = []
    for r in records:
        subjects = db.query(SubjectGrade)\
            .filter(SubjectGrade.semester_record_id == r.id).all()
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
    return {"message": f"Semester {semester_no} deleted."}


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
