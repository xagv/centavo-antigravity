import os

os.environ["AUTH_JWT_SECRET"] = "x" * 32
os.environ["AUTH_DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app import db
db.engine.dispose()
from sqlalchemy import create_engine
db.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db.SessionLocal.configure(bind=db.engine)

from app.main import app  # noqa: E402

db.Base.metadata.create_all(db.engine)
client = TestClient(app)
CRED = {"email": "a@b.com", "password": "supersecret1"}


def test_flow():
    assert client.post("/auth/register", json=CRED).status_code == 201
    assert client.post("/auth/register", json=CRED).status_code == 409
    assert client.post("/auth/login", json={**CRED, "password": "wrongpass12"}).status_code == 401
    token = client.post("/auth/login", json=CRED).json()["access_token"]
    r = client.get("/auth/session", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["email"] == "a@b.com"
    assert "password" not in r.text


def test_session_rejects_invalid():
    assert client.get("/auth/session").status_code == 401
    assert client.get("/auth/session", headers={"Authorization": "Bearer bad"}).status_code == 401
