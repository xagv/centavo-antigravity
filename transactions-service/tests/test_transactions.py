import os

os.environ["TRANSACTIONS_DATABASE_URL"] = "sqlite://"

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
    r = client.post("/transactions", json={"amount": "12.50", "category": " Comida ", "date": "2026-10-01"})
    assert r.status_code == 201
    assert r.json()["category"] == "comida" and r.json()["amount"] == "12.50"
    client.post("/transactions", json={"amount": "30", "category": "transporte", "date": "2026-10-05"})

    all_ = client.get("/transactions").json()
    assert [t["category"] for t in all_] == ["transporte", "comida"]
    assert len(client.get("/transactions", params={"category": "Comida"}).json()) == 1
    assert len(client.get("/transactions", params={"date_from": "2026-10-03"}).json()) == 1


def test_validation():
    base = {"amount": "10", "category": "x", "date": "2026-10-01"}
    assert client.post("/transactions", json={**base, "amount": "-5"}).status_code == 422
    assert client.post("/transactions", json={**base, "category": "  "}).status_code == 422
    assert client.post("/transactions", json={**base, "date": "no-fecha"}).status_code == 422


def test_isolated_per_user():
    client.post("/transactions", json={"amount": "1", "category": "solo-u1", "date": "2026-10-01"})
    current_user["id"] = "user-2"
    try:
        assert all(t["category"] != "solo-u1" for t in client.get("/transactions").json())
    finally:
        current_user["id"] = "user-1"


def test_requires_auth():
    app.dependency_overrides.pop(get_current_user_id)
    try:
        assert client.get("/transactions").status_code == 401
        assert client.post("/transactions", json={}).status_code == 401
    finally:
        app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]