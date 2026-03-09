from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ..database import get_db
from ..services.dependencies import require_teacher
from ..models import User, Student
from ..models.models import SemesterRecord
from ..services.risk_engine import get_student_risk

router = APIRouter(prefix="/teacher", tags=["Teacher"])

class StudentSummary(BaseModel):
    user_id: int
    full_name: str
    roll_number: Optional[str]
    branch: Optional[str]
    current_semester: int
    cgpa: Optional[float]
    class Config:
        from_attributes = True

@router.get("/students", response_model=List[StudentSummary])
def get_all_students(current_user: User = Depends(require_teacher),
                     db: Session = Depends(get_db)):
    result = []
    for s in db.query(Student).all():
        user = db.query(User).filter(User.id == s.user_id).first()
        if user:
            result.append(StudentSummary(
                user_id=user.id, full_name=user.full_name,
                roll_number=user.roll_number, branch=s.branch,
                current_semester=s.current_semester, cgpa=s.cgpa))
    return result


@router.get("/risk-overview")
def get_risk_overview(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns ALL students ranked by SARS score (highest risk first).
    Used by Teacher Risk Monitor dashboard.
    """
    students = db.query(Student).all()
    result = []

    for student in students:
        user = db.query(User).filter(
            User.id == student.user_id
        ).first()
        risk = get_student_risk(student.id, db)

        result.append({
            "student_id": student.id,
            "user_id": student.user_id,
            "full_name": user.full_name if user else "Unknown",
            "roll_number": user.roll_number if user else None,
            "branch": student.branch,
            "current_semester": student.current_semester,
            "cgpa": student.cgpa,
            "sars_score": risk["sars_score"] if risk else None,
            "risk_level": risk["risk_level"] if risk else "UNKNOWN",
            "confidence": risk["confidence"] if risk else None,
            "computed_at": risk["computed_at"] if risk else None,
            "advisory_text": risk["advisory_text"] if risk else None,
        })

    # Sort: HIGH risk first, then MODERATE, WATCH, LOW, UNKNOWN
    risk_order = {
        "HIGH": 0, "MODERATE": 1,
        "WATCH": 2, "LOW": 3, "UNKNOWN": 4
    }
    result.sort(key=lambda x: risk_order.get(x["risk_level"], 4))
    return result


@router.get("/students/{student_id}/risk")
def get_student_risk_detail(
    student_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns full risk breakdown for a specific student.
    Used by Teacher -> click student -> detail view.
    """
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()
    if not student:
        raise HTTPException(404, "Student not found.")

    user = db.query(User).filter(User.id == student.user_id).first()
    risk = get_student_risk(student.id, db)

    # Fetch semester history
    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )
    semester_gpas = [
        {"semester_no": r.semester_no, "gpa": r.gpa}
        for r in records
    ]

    return {
        "student_id": student_id,
        "full_name": user.full_name if user else "Unknown",
        "roll_number": user.roll_number if user else None,
        "branch": student.branch,
        "cgpa": student.cgpa,
        "current_semester": student.current_semester,
        "risk": risk,
        "semester_gpas": semester_gpas,
    }
