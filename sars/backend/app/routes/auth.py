import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from ..database import get_db
from ..services import auth_service
from ..services.dependencies import get_current_user
from ..models import User
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Email format validator ────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

# ── In-memory login brute-force tracker ──────────────────────────────────────
_login_attempts: dict = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 60

def _check_rate_limit(ip: str):
    """Block IPs with > 5 login attempts per 60 seconds."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=_WINDOW_SECONDS)
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
    if len(_login_attempts[ip]) >= _MAX_ATTEMPTS:
        raise HTTPException(
            429,
            "Too many login attempts. Please wait 60 seconds before trying again.",
        )
    _login_attempts[ip].append(now)

# ── Password complexity validator ─────────────────────────────────────────────
def _validate_password_complexity(password: str):
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    if not any(c.isupper() for c in password):
        raise HTTPException(400, "Password must contain at least one uppercase letter.")
    if not any(c.isdigit() for c in password):
        raise HTTPException(400, "Password must contain at least one number.")


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str
    full_name: str
    roll_number: Optional[str] = None
    invite_code: Optional[str] = None
    branch: Optional[str] = None
    enrollment_year: Optional[int] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("student", "teacher"):
            raise ValueError("Role must be student or teacher")
        return v

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    full_name: str
    roll_number: Optional[str] = None
    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()

    # BS-03: Strict email format validation before duplicate check
    if not EMAIL_REGEX.match(email):
        raise HTTPException(400, "Invalid email format.")

    # Teacher invite code check
    if req.role == "teacher":
        if not req.invite_code or req.invite_code != settings.TEACHER_INVITE_CODE:
            raise HTTPException(
                403,
                "Invalid teacher invite code. Contact your administrator.",
            )

    # Password complexity check
    _validate_password_complexity(req.password)

    if auth_service.get_user_by_email(db, email):
        raise HTTPException(400, "Email already registered")

    user = auth_service.create_user(
        db, email, req.password, req.role,
        req.full_name, getattr(req, 'roll_number', None),
    )

    # BS-06: Save role-specific registration fields
    if req.role == "student":
        from ..models.models import Student
        student = db.query(Student).filter(
            Student.user_id == user.id
        ).first()
        if student:
            if getattr(req, 'branch', None):
                student.branch = req.branch
            if getattr(req, 'enrollment_year', None):
                student.enrollment_year = req.enrollment_year
            db.commit()
    elif req.role == "teacher":
        from ..models.models import Teacher
        teacher = db.query(Teacher).filter(
            Teacher.user_id == user.id
        ).first()
        if teacher:
            if getattr(req, 'department', None):
                teacher.department = req.department
            if getattr(req, 'employee_id', None):
                teacher.employee_id = req.employee_id
            db.commit()

    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    user = auth_service.authenticate_user(db, req.email.strip().lower(), req.password)
    if not user:
        raise HTTPException(
            401, "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token(
        {"sub": str(user.id), "role": user.role}
    )
    return TokenResponse(
        access_token=token, role=user.role,
        full_name=user.full_name, user_id=user.id,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
