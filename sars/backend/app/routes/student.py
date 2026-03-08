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
