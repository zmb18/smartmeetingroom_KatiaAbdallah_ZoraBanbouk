import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure test DB and import path
os.environ["DATABASE_URL"] = "sqlite:///./users_test.db"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app import models, crud, schemas, auth  # noqa: E402
from app.deps import engine, SessionLocal  # noqa: E402

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    # seed an admin
    db = SessionLocal()
    try:
        if not crud.get_user_by_username(db, "admin"):
            crud.create_user(db, schemas.UserCreate(username="admin", password="AdminPass123", email="admin@example.com", full_name="Admin User", role="admin"))
    finally:
        db.close()
    yield
    models.Base.metadata.drop_all(bind=engine)
    try:
        os.remove("./users_test.db")
    except FileNotFoundError:
        pass


def auth_header(username: str, role: str):
    token = auth.create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    payload = {"username": "alice", "password": "StrongPass123", "email": "alice@example.com", "full_name": "Alice"}
    r = client.post("/users", json=payload)
    assert r.status_code == 201
    # login
    r = client.post("/token", data={"username": "alice", "password": "StrongPass123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data


def test_list_users_requires_admin():
    r = client.get("/users", headers=auth_header("alice", "regular"))
    assert r.status_code == 403
    r_admin = client.get("/users", headers=auth_header("admin", "admin"))
    assert r_admin.status_code == 200
    assert isinstance(r_admin.json(), list)
