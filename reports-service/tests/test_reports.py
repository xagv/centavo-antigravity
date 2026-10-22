import csv
import io
import json
import os
import tempfile
from datetime import datetime, timezone

_tmp_dir = tempfile.mkdtemp(prefix="centavo_reports_test_")
os.environ["REPORTS_DATABASE_URL"] = "sqlite://"
os.environ["REPORTS_STORAGE_DIR"] = _tmp_dir

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import db, routes  # noqa: E402

db.engine.dispose()
db.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db.SessionLocal.configure(bind=db.engine)

from app.main import app  # noqa: E402
from app.session import get_current_user_id  # noqa: E402

db.Base.metadata.create_all(db.engine)
client = TestClient(app)

current_user = {"id": "user-1"}
app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]


def test_generate_monthly_report_current_month_and_download_files(monkeypatch):
    monkeypatch.setattr(
        routes,
        "fetch_transactions_for_period",
        lambda date_from, date_to, creds: [
            {"id": "tx-1", "amount": "120.50", "category": "Comida", "date": str(date_from)},
            {"id": "tx-2", "amount": "80.00", "category": "comida", "date": str(date_to)},
            {"id": "tx-3", "amount": "45.00", "category": "transporte", "date": str(date_from)},
        ],
    )
    monkeypatch.setattr(
        routes,
        "fetch_budgets",
        lambda creds: [
            {"id": "b-1", "category": "comida", "limit_amount": "150.00", "period": "mensual"},
            {"id": "b-2", "category": "transporte", "limit_amount": "100.00", "period": "mensual"},
        ],
    )

    r = client.post("/reports/monthly")
    assert r.status_code == 201
    body = r.json()

    expected_month = datetime.now(timezone.utc).strftime("%Y-%m")
    assert body["month"] == expected_month
    assert body["total_spent"] == "245.50"
    assert body["total_budget"] == "250.00"
    assert body["transactions_count"] == 3

    cats = {c["category"]: c for c in body["categories"]}
    assert set(cats.keys()) == {"comida", "transporte"}

    assert cats["comida"]["total_spent"] == "200.50"
    assert cats["comida"]["limit_amount"] == "150.00"
    assert cats["comida"]["exceeded_amount"] == "50.50"
    assert cats["comida"]["remaining_amount"] == "0.00"
    assert cats["comida"]["over_budget"] is True

    assert cats["transporte"]["total_spent"] == "45.00"
    assert cats["transporte"]["limit_amount"] == "100.00"
    assert cats["transporte"]["exceeded_amount"] == "0.00"
    assert cats["transporte"]["remaining_amount"] == "55.00"
    assert cats["transporte"]["over_budget"] is False

    # Verificar descarga JSON
    report_id = body["id"]
    r_json = client.get(f"/reports/{report_id}/download?format=json")
    assert r_json.status_code == 200
    assert "application/json" in r_json.headers["content-type"]
    json_file_content = json.loads(r_json.text)
    assert json_file_content["id"] == report_id
    assert json_file_content["total_spent"] == "245.50"

    # Verificar descarga CSV
    r_csv = client.get(f"/reports/{report_id}/download?format=csv")
    assert r_csv.status_code == 200
    assert "text/csv" in r_csv.headers["content-type"]
    reader = list(csv.DictReader(io.StringIO(r_csv.text)))
    assert len(reader) == 2
    assert reader[0]["category"] == "comida"
    assert reader[0]["over_budget"] == "true"
    assert reader[1]["category"] == "transporte"
    assert reader[1]["over_budget"] == "false"


def test_generate_monthly_report_explicit_year_month(monkeypatch):
    monkeypatch.setattr(
        routes,
        "fetch_transactions_for_period",
        lambda date_from, date_to, creds: [
            {"id": "tx-10", "amount": "60.00", "category": "ocio", "date": "2026-02-15"},
        ],
    )
    monkeypatch.setattr(routes, "fetch_budgets", lambda creds: [])

    r = client.post("/reports/monthly", json={"year": 2026, "month": 2})
    assert r.status_code == 201
    body = r.json()
    assert body["month"] == "2026-02"
    assert body["date_from"] == "2026-02-01"
    assert body["date_to"] == "2026-02-28"
    assert body["total_spent"] == "60.00"
    assert body["total_budget"] == "0.00"
    assert body["categories"][0]["limit_amount"] is None
    assert body["categories"][0]["over_budget"] is False


def test_validation_incomplete_period():
    assert client.post("/reports/monthly", json={"year": 2026}).status_code == 422
    assert client.post("/reports/monthly", json={"month": 5}).status_code == 422
    assert client.post("/reports/monthly", json={"year": 2026, "month": 13}).status_code == 422


def test_isolated_per_user(monkeypatch):
    monkeypatch.setattr(routes, "fetch_transactions_for_period", lambda df, dt, creds: [])
    monkeypatch.setattr(routes, "fetch_budgets", lambda creds: [])

    created = client.post("/reports/monthly", json={"year": 2026, "month": 3}).json()
    report_id = created["id"]

    current_user["id"] = "user-2"
    try:
        assert all(rep["id"] != report_id for rep in client.get("/reports").json())
        assert client.get(f"/reports/{report_id}").status_code == 404
        assert client.get(f"/reports/{report_id}/download?format=json").status_code == 404
    finally:
        current_user["id"] = "user-1"


def test_requires_auth():
    app.dependency_overrides.pop(get_current_user_id)
    try:
        assert client.get("/reports").status_code == 401
        assert client.post("/reports/monthly").status_code == 401
    finally:
        app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]
