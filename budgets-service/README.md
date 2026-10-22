# budgets-service

Definición y consulta de presupuestos por categoría para Centavo (FastAPI + SQLAlchemy).

## Directivas
- Toda ruta exige sesión; los datos se filtran siempre por el usuario autenticado.
- La sesión se valida en `app/session.py` consultando `GET /auth/session` de auth-service. Este servicio no decodifica tokens ni conoce el secreto JWT.
- No se loguean tokens.

## Endpoints
- `POST /budgets` - `{category, limit_amount, period}` (`limit_amount` > 0, 2 decimales; `category` y `period` normalizados a minúsculas)
- `GET /budgets` - lista de presupuestos del usuario, más recientes primero. Filtros: `category`, `period`, `limit`, `offset`

## Uso
`pip install -r requirements.txt`, definir `BUDGETS_AUTH_SERVICE_URL` (ver `.env.example`),
`uvicorn app.main:app --port 8002`. Tests: `pytest`.
