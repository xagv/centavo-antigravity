import os

os.environ["BUDGETS_DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app import db

db.engine.dispose()
db.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db.SessionLocal.configure(bind=db.engine)

from app.main import app  # noqa: E402
from app.session import get_current_user_id  # noqa: E402

db.Base.metadata.create_all(db.engine)
client = TestClient(app)

current_user = {"id": "user-1"}
app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]


def test_create_and_list():
    r = client.post(
        "/budgets",
        json={"category": " Comida ", "limit_amount": "500.00", "period": " Mensual "},
    )
    assert r.status_code == 201
    assert r.json()["category"] == "comida"
    assert r.json()["limit_amount"] == "500.00"
    assert r.json()["period"] == "mensual"

    client.post(
        "/budgets",
        json={"category": "transporte", "limit_amount": "150", "period": "semanal"},
    )

    all_ = client.get("/budgets").json()
    assert len(all_) == 2
    assert {b["category"] for b in all_} == {"comida", "transporte"}
    assert len(client.get("/budgets", params={"category": "Comida"}).json()) == 1
    assert len(client.get("/budgets", params={"period": "Semanal"}).json()) == 1


def test_validation():
    base = {"category": "ocio", "limit_amount": "100", "period": "mensual"}
    assert client.post("/budgets", json={**base, "limit_amount": "-5"}).status_code == 422
    assert client.post("/budgets", json={**base, "limit_amount": "0"}).status_code == 422
    assert client.post("/budgets", json={**base, "category": "  "}).status_code == 422
    assert client.post("/budgets", json={**base, "period": "  "}).status_code == 422


def test_isolated_per_user():
    client.post("/budgets", json={"category": "solo-u1", "limit_amount": "50", "period": "mensual"})
    current_user["id"] = "user-2"
    try:
        assert all(b["category"] != "solo-u1" for b in client.get("/budgets").json())
    finally:
        current_user["id"] = "user-1"


def test_requires_auth():
    app.dependency_overrides.pop(get_current_user_id)
    try:
        assert client.get("/budgets").status_code == 401
        assert client.post("/budgets", json={}).status_code == 401
    finally:
        app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]
