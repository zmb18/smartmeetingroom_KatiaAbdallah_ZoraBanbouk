import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Isolated SQLite DB for tests before importing app
os.environ["DATABASE_URL"] = "sqlite:///./reviews_test.db"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app.deps import engine  # noqa: E402
from app import models, auth  # noqa: E402

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)
    try:
        os.remove("./reviews_test.db")
    except FileNotFoundError:
        pass


def auth_header(user_id: int = 1, role: str = "regular"):
    token = auth.create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_post_review_requires_auth():
    payload = {"user_id": 1, "room_id": 1, "rating": 5, "comment": "Great room"}
    r = client.post("/rooms/1/reviews", json=payload)
    assert r.status_code in (401, 422)


def test_create_update_delete_review_with_roles():
    payload = {"user_id": 1, "room_id": 1, "rating": 4, "comment": "Nice room"}
    r = client.post("/rooms/1/reviews", json=payload, headers=auth_header())
    assert r.status_code == 200
    review_id = r.json()["id"]

    # update by owner
    r_upd = client.put(f"/reviews/{review_id}", json={"comment": "Updated"}, headers=auth_header())
    assert r_upd.status_code == 200
    assert r_upd.json()["comment"] == "Updated"

    # delete by regular (owner) succeeds per current logic
    r_del_forbidden = client.delete(f"/reviews/{review_id}", headers=auth_header(user_id=2))
    assert r_del_forbidden.status_code in (403, 404)

    r_del_admin = client.delete(f"/reviews/{review_id}", headers=auth_header(user_id=99, role="admin"))
    assert r_del_admin.status_code == 204


def test_post_flag_and_moderate_review():
    payload = {"user_id": 1, "room_id": 1, "rating": 4, "comment": "Nice room"}
    r = client.post("/rooms/1/reviews", json=payload, headers=auth_header())
    assert r.status_code == 200
    review = r.json()
    review_id = review["id"]

    # flag by any authenticated user
    r_flag = client.post(f"/reviews/{review_id}/flag", headers=auth_header(username="bob"))
    assert r_flag.status_code == 200
    assert r_flag.json()["flagged"] is True

    # moderate (hide) by moderator/admin
    mod_header = auth_header(username="mod", role="moderator")
    r_mod = client.put(f"/reviews/{review_id}/moderate", params={"hide": True}, headers=mod_header)
    assert r_mod.status_code == 200
    assert r_mod.json()["hidden"] is True
def test_user_reviews_authorization():
    """Test that users can only view their own reviews"""
    # User 1 creates review
    payload = {"rating": 5, "comment": "Great"}
    r1 = client.post("/rooms/1/reviews", json=payload, headers=auth_header(user_id=1))
    
    # User 2 tries to view User 1's reviews - should fail
    r2 = client.get("/users/1/reviews", headers=auth_header(user_id=2))
    assert r2.status_code == 403
    
    # Admin can view anyone's reviews
    r3 = client.get("/users/1/reviews", headers=auth_header(user_id=99, role="admin"))
    assert r3.status_code == 200