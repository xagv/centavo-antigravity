"""Hashing de contraseñas (Argon2id) y emisión de tokens."""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from .config import settings

# Argon2id con parámetros por defecto de argon2-cffi (RFC 9106, perfil low-memory).
_hasher = PasswordHasher()
# Hash ficticio para igualar tiempos cuando el usuario no existe.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        _hasher.verify(password_hash or _DUMMY_HASH, password)
        return password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def issue_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=settings.token_ttl_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
