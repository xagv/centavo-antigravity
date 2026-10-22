# auth-service

Registro, login y verificación de sesión para Centavo (FastAPI + SQLAlchemy).

## Directivas
- Nunca se loguean credenciales ni tokens.
- Toda validación de sesión pasa por `app/session.py` (único módulo).
- Hashing: Argon2id (`app/security.py`). Cambios requieren justificación explícita en el plan.

## Endpoints
- `POST /auth/register` - `{email, password}`
- `POST /auth/login` - devuelve JWT Bearer
- `GET /auth/session` - valida el token y devuelve el usuario

## Uso
`pip install -r requirements.txt`, definir `AUTH_JWT_SECRET` (ver `.env.example`),
`uvicorn app.main:app`. Tests: `pytest`.
