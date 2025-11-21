import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import pytest

# Isolated SQLite DB for tests before importing app
os.environ["DATABASE_URL"] = "sqlite:///./bookings_test.db"
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
        os.remove("./bookings_test.db")
    except FileNotFoundError:
        pass


def auth_header(user_id: int = 1, role: str = "regular"):
    token = auth.create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_create_booking_requires_auth():
    payload = {
        "user_id": 1,
        "room_id": 1,
        "start_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
    }
    r = client.post("/bookings", json=payload)
    assert r.status_code in (401, 403)


def test_create_conflict_and_cancel_booking():
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=1)
    payload = {"user_id": 1, "room_id": 1, "start_time": start.isoformat(), "end_time": end.isoformat()}
    r = client.post("/bookings", json=payload, headers=auth_header())
    assert r.status_code == 200
    data = r.json()
    booking_id = data["id"]
    assert data["status"] == "booked"

    # overlapping booking should conflict
    r2 = client.post("/bookings", json=payload, headers=auth_header(user_id=2))
    assert r2.status_code == 409

    # cancel by owner
    r_cancel = client.post(f"/bookings/{booking_id}/cancel", headers=auth_header(user_id=1))
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "cancelled"

    # list requires admin/manager/auditor
    r_list_forbidden = client.get("/bookings", headers=auth_header(user_id=1))
    assert r_list_forbidden.status_code == 403
    r_list = client.get("/bookings", headers=auth_header(user_id=99, role="admin"))
    assert r_list.status_code == 200
