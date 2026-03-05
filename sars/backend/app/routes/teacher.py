from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ..database import get_db
from ..services.dependencies import require_teacher
from ..models import User, Student

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
