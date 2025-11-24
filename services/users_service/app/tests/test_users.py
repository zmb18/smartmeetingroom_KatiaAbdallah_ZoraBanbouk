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
def test_update_user():
    """Test updating user profile"""
    # Create user
    payload = {"username": "bob", "password": "BobPass123", "email": "bob@example.com"}
    client.post("/users", json=payload)
    
    # Update own profile
    update_payload = {"full_name": "Bob Smith"}
    r = client.put("/users/bob", json=update_payload, headers=auth_header("bob", "regular"))
    assert r.status_code == 200
    assert r.json()["full_name"] == "Bob Smith"

def test_delete_user():
    """Test deleting user account"""
    payload = {"username": "charlie", "password": "CharliePass123", "email": "charlie@example.com"}
    client.post("/users", json=payload)
    
    # User can delete own account
    r = client.delete("/users/charlie", headers=auth_header("charlie", "regular"))
    assert r.status_code == 204
    
    # Verify user is deleted
    r = client.get("/users/charlie", headers=auth_header("admin", "admin"))
    assert r.status_code == 404

def test_username_validation():
    """Test username validation rules"""
    # Invalid username with special chars
    payload = {"username": "user@name", "password": "Pass123", "email": "test@example.com"}
    r = client.post("/users", json=payload)
    assert r.status_code == 422
    
    # Valid username with underscore
    payload = {"username": "user_name", "password": "Pass123", "email": "test2@example.com"}
    r = client.post("/users", json=payload)
    assert r.status_code == 201

def test_email_uniqueness():
    """Test email must be unique"""
    payload1 = {"username": "user1", "password": "Pass123", "email": "same@example.com"}
    payload2 = {"username": "user2", "password": "Pass123", "email": "same@example.com"}
    
    r1 = client.post("/users", json=payload1)
    assert r1.status_code == 201
    
    r2 = client.post("/users", json=payload2)
    assert r2.status_code == 400
    assert "email" in r2.json()["detail"].lower()
