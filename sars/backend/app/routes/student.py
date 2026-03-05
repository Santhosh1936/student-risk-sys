import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.dependencies import require_student
from ..models import User, Student
from ..models.models import SemesterRecord, SubjectGrade
from ..services.grade_extractor import extract_from_file

router = APIRouter(prefix="/student", tags=["Student"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


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


@router.get("/profile", response_model=StudentProfileResponse)
def get_student_profile(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
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


@router.post("/debug-extract")
async def debug_extract(
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
):
    """Returns the raw extracted text from the uploaded file (for debugging)."""
    from ..services.grade_extractor import extract_text_from_file
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{ext}' not allowed.")
    contents = await file.read()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"debug_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        raw_text = extract_text_from_file(file_path)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    return {"raw_text": raw_text, "length": len(raw_text), "lines": raw_text.split("\n")}


@router.post("/upload-marksheet")
async def upload_marksheet(
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{ext}' not allowed. Use PDF, JPG, or PNG.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum size is 10 MB.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        parsed = extract_from_file(file_path)
    except ValueError as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(422, str(e))
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(500, f"Extraction failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(404, "Student profile not found")

    semester_no = parsed.get("semester_no") or 1

    existing = db.query(SemesterRecord).filter(
        SemesterRecord.student_id == student.id,
        SemesterRecord.semester_no == semester_no,
    ).first()
    if existing:
        raise HTTPException(
            409,
            f"Semester {semester_no} already uploaded. "
            "Delete the existing record before re-uploading.",
        )

    semester_record = SemesterRecord(
        student_id=student.id,
        semester_no=semester_no,
        gpa=parsed.get("sgpa"),
        credits_attempted=len(parsed.get("subjects", [])),
        credits_earned=parsed.get("total_credits"),
        is_confirmed=True,
    )
    db.add(semester_record)
    db.flush()

    for subj in parsed.get("subjects", []):
        db.add(SubjectGrade(
            semester_record_id=semester_record.id,
            subject_name=subj["subject_name"],
            subject_code=subj["subject_code"],
            grade_letter=subj["grade_letter"],
            grade_points=subj["grade_points"],
            credits=subj["credits"],
            is_backlog=subj["is_backlog"],
        ))

    cgpa = parsed.get("cgpa") or parsed.get("sgpa")
    if cgpa:
        student.cgpa = cgpa
    if semester_no >= (student.current_semester or 1):
        student.current_semester = semester_no

    db.commit()
    db.refresh(semester_record)

    subjects = parsed.get("subjects", [])
    return {
        "message": "Marksheet uploaded and parsed successfully",
        "semester_no": semester_no,
        "semester_record_id": semester_record.id,
        "sgpa": parsed.get("sgpa"),
        "cgpa": cgpa,
        "subjects_extracted": len(subjects),
        "subjects": subjects,
        "hall_ticket_no": parsed.get("hall_ticket_no"),
        "exam_month_year": parsed.get("exam_month_year"),
        "extraction_note": (
            "Parsed successfully"
            if len(subjects) >= 3
            else "Partial extraction — please verify subject data"
        ),
    }


@router.get("/semesters")
def get_student_semesters(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return []

    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student.id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )

    result = []
    for r in records:
        subjects = (
            db.query(SubjectGrade)
            .filter(SubjectGrade.semester_record_id == r.id)
            .all()
        )
        result.append({
            "semester_no":        r.semester_no,
            "semester_record_id": r.id,
            "gpa":                r.gpa,
            "credits_earned":     r.credits_earned,
            "uploaded_at":        r.uploaded_at.isoformat() if r.uploaded_at else None,
            "subjects": [
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "grade_letter": s.grade_letter,
                    "grade_points": s.grade_points,
                    "credits":      s.credits,
                    "is_backlog":   s.is_backlog,
                }
                for s in subjects
            ],
        })

    return result
