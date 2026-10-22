import os
from decimal import Decimal

os.environ["NOTIFICATIONS_DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app import db, routes

db.engine.dispose()
db.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db.SessionLocal.configure(bind=db.engine)

from app.main import app  # noqa: E402
from app.session import get_current_user_id  # noqa: E402

db.Base.metadata.create_all(db.engine)
client = TestClient(app)

current_user = {"id": "user-1"}
app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]


def test_evaluate_transaction_triggers_alert_with_explicit_limit():
    r = client.post(
        "/notifications/transactions",
        json={
            "amount": "150.00",
            "category": " Comida ",
            "current_spent": "400.00",
            "limit_amount": "500.00",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["alert_triggered"] is True
    assert body["category"] == "comida"
    assert body["total_spent"] == "550.00"
    assert body["limit_amount"] == "500.00"
    assert body["exceeded_amount"] == "50.00"
    assert body["notification"] is not None
    assert body["notification"]["category"] == "comida"


def test_evaluate_transaction_within_budget_does_not_trigger_alert():
    r = client.post(
        "/notifications/transactions",
        json={
            "amount": "80.00",
            "category": "transporte",
            "current_spent": "50.00",
            "limit_amount": "200.00",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["alert_triggered"] is False
    assert body["total_spent"] == "130.00"
    assert body["exceeded_amount"] == "0.00"
    assert body["notification"] is None


def test_evaluate_transaction_fetches_budget_from_service(monkeypatch):
    monkeypatch.setattr(
        routes,
        "fetch_budget_limit",
        lambda category, period, creds: Decimal("300.00") if category == "ocio" else None,
    )
    r = client.post(
        "/notifications/events/transaction",
        json={"amount": "350.00", "category": "Ocio", "period": "Mensual"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["alert_triggered"] is True
    assert body["limit_amount"] == "300.00"
    assert body["exceeded_amount"] == "50.00"


def test_validation():
    base = {"amount": "100.00", "category": "ocio", "limit_amount": "50.00"}
    assert client.post("/notifications/transactions", json={**base, "amount": "-5"}).status_code == 422
    assert client.post("/notifications/transactions", json={**base, "amount": "0"}).status_code == 422
    assert client.post("/notifications/transactions", json={**base, "category": "  "}).status_code == 422


def test_isolated_per_user():
    client.post(
        "/notifications/transactions",
        json={"amount": "100.00", "category": "solo-u1", "limit_amount": "50.00"},
    )
    current_user["id"] = "user-2"
    try:
        assert all(n["category"] != "solo-u1" for n in client.get("/notifications").json())
    finally:
        current_user["id"] = "user-1"


def test_requires_auth():
    app.dependency_overrides.pop(get_current_user_id)
    try:
        assert client.get("/notifications").status_code == 401
        assert client.post("/notifications/transactions", json={}).status_code == 401
    finally:
        app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]
