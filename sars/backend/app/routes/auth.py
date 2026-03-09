import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from ..database import get_db
from ..services import auth_service
from ..services.dependencies import get_current_user
from ..models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str
    full_name: str
    roll_number: str = None

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

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
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
    if auth_service.get_user_by_email(db, req.email):
        raise HTTPException(400, "Email already registered")
    return auth_service.create_user(db, req.email, req.password, req.role,
                                    req.full_name, req.roll_number)

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(401, "Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    token = auth_service.create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, role=user.role,
                         full_name=user.full_name, user_id=user.id)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
