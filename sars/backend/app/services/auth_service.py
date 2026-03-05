# backend/app/services/auth_service.py
#
# ALL auth logic lives here — routes stay thin and just call this.
#
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt as _bcrypt
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, Student, Teacher


# ── Password helpers ────────────────────────────────────────────────────────
# Use bcrypt directly (no passlib) to avoid passlib+bcrypt≥4.1 incompatibility.
# BUG 3 FIX: explicit 72-byte truncation before bcrypt (bcrypt limit).

def _truncate(plain: str) -> bytes:
    """Return password bytes, capped at 72 bytes (bcrypt hard limit)."""
    return plain.encode("utf-8")[:72]

def hash_password(plain: str) -> str:
    hashed = _bcrypt.hashpw(_truncate(plain), _bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(_truncate(plain), hashed.encode("utf-8"))


# ── JWT helpers ─────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT. Always include: sub (user id), role, exp.
    Never put sensitive data (passwords, secrets) inside the token.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


# ── DB helpers ──────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower().strip()).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, email: str, password: str, role: str,
                full_name: str, roll_number: str = None) -> User:
    user = User(email=email.lower().strip(), password_hash=hash_password(password),
                role=role, full_name=full_name, roll_number=roll_number)
    db.add(user)
    db.flush()
    if role == "student":
        db.add(Student(user_id=user.id))
    elif role == "teacher":
        db.add(Teacher(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
