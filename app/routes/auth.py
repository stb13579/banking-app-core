import base64
import hashlib
import os
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import jwt

from app.database import get_db
from app.models import User
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret123")
JWT_ALGORITHM = "HS256"


def _md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=_md5(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    password_hash = _md5(payload.password)

    query = (
        f"SELECT id, username, email, role FROM users "
        f"WHERE username = '{payload.username}' "
        f"AND password_hash = '{password_hash}'"
    )
    row = db.execute(text(query)).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {"sub": row.id, "username": row.username, "role": row.role},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {"access_token": token}


@router.post("/reset-password/request")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    raw = f"{user.id}:{int(time.time())}"
    token = base64.b64encode(raw.encode()).decode()

    return {"reset_token": token, "message": "Use this token to reset your password"}


@router.post("/reset-password/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    try:
        decoded = base64.b64decode(payload.token.encode()).decode()
        user_id, _ts = decoded.split(":", 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = _md5(payload.new_password)
    db.commit()
    return {"message": "Password reset successfully"}
