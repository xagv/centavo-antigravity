"""Identifica al usuario delegando en auth-service (GET /auth/session).

Este servicio NO decodifica tokens ni conoce el secreto JWT: la validación de
sesión vive únicamente en auth-service.
"""
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = HTTPException(
    status.HTTP_401_UNAUTHORIZED, "Sesión inválida", headers={"WWW-Authenticate": "Bearer"}
)


def get_current_user_id(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """Devuelve el user_id del token según auth-service o lanza 401."""
    if creds is None:
        raise _UNAUTHORIZED
    try:
        resp = httpx.get(
            f"{settings.auth_service_url}/auth/session",
            headers={"Authorization": f"Bearer {creds.credentials}"},
            timeout=5.0,
        )
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "auth-service no disponible")
    if resp.status_code != 200:
        raise _UNAUTHORIZED
    return resp.json()["id"]