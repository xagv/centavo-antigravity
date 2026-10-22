# transactions-service

Registro y categorización de gastos para Centavo (FastAPI + SQLAlchemy).

## Directivas
- Toda ruta exige sesión; los datos se filtran siempre por el usuario autenticado.
- La sesión se valida en `app/session.py` consultando `GET /auth/session` de auth-service. Este servicio no decodifica tokens ni conoce el secreto JWT.
- No se loguean tokens.

## Endpoints
- `POST /transactions` - `{amount, category, date}` (amount > 0, 2 decimales; categoría normalizada a minúsculas)
- `GET /transactions` - lista del usuario, más recientes primero. Filtros: `category`, `date_from`, `date_to`, `limit`, `offset`

## Uso
`pip install -r requirements.txt`, definir `TRANSACTIONS_AUTH_SERVICE_URL` (ver `.env.example`),
`uvicorn app.main:app --port 8001`. Tests: `pytest`.