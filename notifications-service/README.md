# notifications-service

Generación y consulta de alertas de sobregasto para Centavo (FastAPI + SQLAlchemy).

## Directivas
- Toda ruta exige sesión; los datos se filtran siempre por el usuario autenticado.
- La sesión se valida en `app/session.py` consultando `GET /auth/session` de auth-service. Este servicio no decodifica tokens ni conoce el secreto JWT.
- Si el evento de transacción no incluye `limit_amount`, consulta el presupuesto correspondiente en `budgets-service` (`GET /budgets`).
- No se loguean tokens.

## Endpoints
- `POST /notifications/transactions` (alias `POST /notifications/events/transaction`) - recibe un evento de nueva transacción `{amount, category, period?, date?, current_spent?, limit_amount?}`, evalúa contra el presupuesto correspondiente y genera una alerta si `current_spent + amount > limit_amount`.
- `GET /notifications` - lista de alertas generadas del usuario, más recientes primero. Filtros: `category`, `limit`, `offset`.

## Uso
`pip install -r requirements.txt`, definir `NOTIFICATIONS_AUTH_SERVICE_URL` y `NOTIFICATIONS_BUDGETS_SERVICE_URL` (ver `.env.example`),
`uvicorn app.main:app --port 8003`. Tests: `pytest`.
