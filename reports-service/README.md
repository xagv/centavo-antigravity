# reports-service

Generación bajo demanda y consulta de reportes mensuales de gastos para Centavo (FastAPI + SQLAlchemy).

## Directivas
- Toda ruta exige sesión; los datos y archivos se filtran siempre por el usuario autenticado.
- La sesión se valida en `app/session.py` consultando `GET /auth/session` de auth-service. Este servicio no decodifica tokens ni conoce el secreto JWT.
- Consulta las transacciones del período en `transactions-service` (`GET /transactions`) y los límites configurados en `budgets-service` (`GET /budgets`).
- Persiste cada reporte generado como archivo en disco (formatos JSON y CSV dentro de `REPORTS_STORAGE_DIR`) y guarda sus metadatos en SQLite para consulta y descarga posterior.
- No se loguean tokens.

## Endpoints
- `POST /reports/monthly` - genera el reporte mensual bajo demanda (por defecto del mes actual, o especificando `{year, month}` opcionalmente). Guarda los archivos `.json` y `.csv` y registra el reporte.
- `GET /reports` - lista de reportes generados del usuario, más recientes primero. Filtros: `month` (`YYYY-MM`), `limit`, `offset`.
- `GET /reports/{report_id}` - detalle de un reporte específico del usuario.
- `GET /reports/{report_id}/download` - descarga el archivo generado (`?format=json` o `?format=csv`).

## Uso
`pip install -r requirements.txt`, definir `REPORTS_AUTH_SERVICE_URL`, `REPORTS_TRANSACTIONS_SERVICE_URL` y `REPORTS_BUDGETS_SERVICE_URL` (ver `.env.example`),
`uvicorn app.main:app --port 8004`. Tests: `pytest`.
