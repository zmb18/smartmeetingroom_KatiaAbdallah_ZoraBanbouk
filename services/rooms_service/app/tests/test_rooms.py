import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Use isolated SQLite DB for tests before importing app
os.environ["DATABASE_URL"] = "sqlite:///./rooms_test.db"
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
        os.remove("./rooms_test.db")
    except FileNotFoundError:
        pass


def auth_header(role: str = "admin", username: str = "admin"):
    token = auth.create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_create_room_requires_token():
    payload = {"name": "Room A", "capacity": 10, "equipment": ["projector"], "location": "1st floor"}
    r = client.post("/rooms", json=payload)
    assert r.status_code in (401, 403)


def test_create_update_delete_room_with_roles():
    payload = {"name": "Room A", "capacity": 10, "equipment": ["projector"], "location": "1st floor"}
    r = client.post("/rooms", json=payload, headers=auth_header())
    assert r.status_code == 200
    room_id = r.json()["id"]

    # update with manager
    r_upd = client.put(f"/rooms/{room_id}", json={"capacity": 20}, headers=auth_header(role="manager"))
    assert r_upd.status_code == 200
    assert r_upd.json()["capacity"] == 20

    # delete with regular should fail
    r_del_fail = client.delete(f"/rooms/{room_id}", headers=auth_header(role="regular"))
    assert r_del_fail.status_code == 403

    r_del = client.delete(f"/rooms/{room_id}", headers=auth_header())
    assert r_del.status_code == 204


def test_list_rooms_filters_capacity():
    # seed one room
    client.post("/rooms", json={"name": "Room B", "capacity": 5}, headers=auth_header())
    r = client.get("/rooms?capacity=5")
    assert r.status_code == 200
    rooms = r.json()
    assert len(rooms) >= 1
