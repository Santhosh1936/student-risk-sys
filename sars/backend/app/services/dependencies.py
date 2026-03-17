from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import get_db
from .auth_service import decode_token, get_user_by_id
from ..models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    exc = HTTPException(status_code=401, detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(token)
    if not payload: raise exc
    user_id = payload.get("sub")
    if not user_id: raise exc
    user = get_user_by_id(db, int(user_id))
    if not user: raise exc
    if not user.is_active:
        raise HTTPException(
            403,
            "This account has been deactivated. Contact your administrator."
        )
    return user

def require_student(u: User = Depends(get_current_user)) -> User:
    if u.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return u

def require_teacher(u: User = Depends(get_current_user)) -> User:
    if u.role != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    return u
