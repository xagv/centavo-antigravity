"""ÚNICO módulo de validación de sesión. Ningún otro módulo debe decodificar tokens."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = HTTPException(
    status.HTTP_401_UNAUTHORIZED, "Sesión inválida", headers={"WWW-Authenticate": "Bearer"}
)


def validate_token(token: str) -> str:
    """Devuelve el user_id del token o lanza 401."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=["HS256"], options={"require": ["sub", "exp"]}
        )
    except jwt.PyJWTError:
        raise _UNAUTHORIZED
    return payload["sub"]


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _UNAUTHORIZED
    user = db.get(User, validate_token(creds.credentials))
    if user is None:
        raise _UNAUTHORIZED
    return user
