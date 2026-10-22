from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import security
from .db import get_db
from .models import User
from .schemas import Credentials, TokenOut, UserOut
from .session import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: Credentials, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se pudo registrar el usuario")
    user = User(email=email, password_hash=security.hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "No se pudo registrar el usuario")
    return user


@router.post("/login", response_model=TokenOut)
def login(data: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not security.verify_password(user.password_hash if user else None, data.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
    if security.needs_rehash(user.password_hash):
        user.password_hash = security.hash_password(data.password)
        db.commit()
    return TokenOut(access_token=security.issue_token(user.id))


@router.get("/session", response_model=UserOut)
def session(user: User = Depends(get_current_user)):
    return user
