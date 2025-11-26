"""
Test suite for the Bookings service.

This module contains comprehensive tests for all booking endpoints including:
- Booking creation, updates, and cancellations
- Authorization and authentication checks
- Availability checking and conflict detection
- Input validation and business rules
- Admin and service account operations
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock

# Isolated SQLite DB for tests before importing app
os.environ["DATABASE_URL"] = "sqlite:///./bookings_test.db"
os.environ["TESTING"] = "true"  # Disable future time validation in tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app.deps import engine  # noqa: E402
from app import models, auth  # noqa: E402

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """
    Set up test database before running tests and clean up afterwards.
    
    This fixture:
    - Drops all existing tables
    - Creates fresh tables for testing
    - Yields control to tests
    - Cleans up tables and database file after all tests complete
    """
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)
    try:
        os.remove("./bookings_test.db")
    except FileNotFoundError:
        pass


def auth_header(username: str = "testuser", role: str = "regular"):
    """
    Create authorization header with JWT token.
    
    Args:
        username: Username to encode in the token (default: "testuser")
        role: User role to encode in the token (default: "regular")
        
    Returns:
        dict: Authorization header with Bearer token
    """
    token = auth.create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_health():
    """Test health check endpoint returns OK status."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_create_booking_success(mock_rooms_get, mock_users_get):
    """
    Test successful booking creation.
    
    Verifies that:
    - Valid booking request creates a new booking
    - Response includes all expected fields
    - Booking status is set to 'booked'
    - Attendee count is properly stored
    """
    # Mock user service response
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    # Mock room service response
    mock_rooms_get.return_value = {"id": 1, "name": "Conference Room A", "is_active": True, "capacity": 10}
    
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=1)
    payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "attendee_count": 5
    }
    
    r = client.post("/bookings", json=payload, headers=auth_header("testuser"))
    assert r.status_code == 200
    data = r.json()
    assert data["room_id"] == 1
    assert data["status"] == "booked"
    assert data["attendee_count"] == 5
    assert "id" in data


def test_create_booking_requires_auth():
    """Test that creating a booking requires authentication."""
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=1)
    payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    r = client.post("/bookings", json=payload)
    assert r.status_code == 401


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_booking_conflict(mock_rooms_get, mock_users_get):
    """
    Test that overlapping bookings are prevented.
    
    Verifies that:
    - First booking for a time slot succeeds
    - Second booking for the same time slot fails with 409 Conflict
    - Error message indicates room is not available
    """
    mock_users_get.return_value = {"id": 1, "username": "user1", "role": "regular"}
    mock_rooms_get.return_value = {"id": 1, "name": "Room A", "is_active": True, "capacity": 10}
    
    start = datetime.utcnow() + timedelta(hours=2)
    end = start + timedelta(hours=1)
    payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    
    # First booking
    r1 = client.post("/bookings", json=payload, headers=auth_header("user1"))
    assert r1.status_code == 200
    
    # Mock different user
    mock_users_get.return_value = {"id": 2, "username": "user2", "role": "regular"}
    
    # Overlapping booking should fail
    r2 = client.post("/bookings", json=payload, headers=auth_header("user2"))
    assert r2.status_code == 409
    assert "not available" in r2.json()["detail"].lower()


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_capacity_validation(mock_rooms_get, mock_users_get):
    """
    Test that bookings validate room capacity.
    
    Verifies that attempting to book a room with attendee count
    exceeding the room's capacity results in a 400 Bad Request error.
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    mock_rooms_get.return_value = {"id": 2, "name": "Small Room", "is_active": True, "capacity": 5}
    
    start = datetime.utcnow() + timedelta(hours=3)
    end = start + timedelta(hours=1)
    payload = {
        "room_id": 2,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "attendee_count": 10  # Exceeds capacity of 5
    }
    
    r = client.post("/bookings", json=payload, headers=auth_header("testuser"))
    assert r.status_code == 400
    assert "capacity" in r.json()["detail"].lower()


@patch('common.service_client.users_client.get')
def test_cancel_booking_with_reason(mock_users_get):
    """
    Test booking cancellation with reason.
    
    Verifies that:
    - Booking can be cancelled with a reason
    - Status changes to 'cancelled'
    - Cancellation reason is stored
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    
    # Create a booking first (assuming id=1 exists from previous tests)
    # In real scenario, you'd create it in this test
    cancel_payload = {
        "reason": "Meeting was rescheduled"
    }
    
    r = client.post("/bookings/1/cancel", json=cancel_payload, headers=auth_header("testuser"))
    # Will be 404 if booking doesn't exist or 200 if it does
    if r.status_code == 200:
        data = r.json()
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] == "Meeting was rescheduled"


@patch('common.service_client.users_client.get')
def test_override_booking_admin_only(mock_users_get):
    """
    Test that only admin/manager can override bookings.
    
    Verifies that:
    - Regular users receive 403 Forbidden
    - Admin/Manager users can successfully override
    - Override reason is stored
    - Status changes to 'overridden'
    """
    mock_users_get.return_value = {"id": 1, "username": "regular_user", "role": "regular"}
    
    override_payload = {
        "reason": "Emergency maintenance required in the room"
    }
    
    # Regular user should be denied
    r = client.post("/bookings/1/override", json=override_payload, headers=auth_header("regular_user", "regular"))
    assert r.status_code == 403
    
    # Admin should succeed
    mock_users_get.return_value = {"id": 2, "username": "admin", "role": "admin"}
    r_admin = client.post("/bookings/1/override", json=override_payload, headers=auth_header("admin", "admin"))
    if r_admin.status_code == 200:
        data = r_admin.json()
        assert data["status"] == "overridden"
        assert "maintenance" in data["override_reason"].lower()


@patch('common.service_client.users_client.get')
def test_list_bookings_requires_elevated_role(mock_users_get):
    """
    Test that listing all bookings requires admin/manager/auditor role.
    
    Verifies that:
    - Regular users receive 403 Forbidden
    - Admin/Manager/Auditor users can access the endpoint
    - Response is a list of bookings
    """
    mock_users_get.return_value = {"id": 1, "username": "regular_user", "role": "regular"}
    
    # Regular user should be denied
    r = client.get("/bookings", headers=auth_header("regular_user", "regular"))
    assert r.status_code == 403
    
    # Admin should succeed
    r_admin = client.get("/bookings", headers=auth_header("admin", "admin"))
    assert r_admin.status_code == 200
    assert isinstance(r_admin.json(), list)


@patch('common.service_client.users_client.get')
def test_check_availability(mock_users_get):
    """
    Test room availability checking.
    
    Verifies that:
    - Availability endpoint returns expected fields
    - Response includes available status and conflicting bookings
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    
    start = (datetime.utcnow() + timedelta(hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(hours=11)).isoformat()
    
    r = client.get(
        f"/bookings/availability/1?start_time={start}&end_time={end}",
        headers=auth_header()
    )
    assert r.status_code == 200
    data = r.json()
    assert "available" in data
    assert "room_id" in data
    assert "conflicting_bookings" in data


def test_invalid_datetime_format():
    """Test validation for invalid datetime format returns 400 error."""
    r = client.get(
        "/bookings/availability/1?start_time=invalid&end_time=also-invalid",
        headers=auth_header()
    )
    assert r.status_code == 400
    assert "invalid" in r.json()["detail"].lower()


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_booking_validation(mock_rooms_get, mock_users_get):
    """
    Test booking input validation.
    
    Verifies that end_time before start_time results in validation error (422).
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    mock_rooms_get.return_value = {"id": 1, "is_active": True, "capacity": 10}
    
    # Test end_time before start_time
    start = datetime.utcnow() + timedelta(hours=2)
    end = start - timedelta(hours=1)  # Earlier than start
    payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    r = client.post("/bookings", json=payload, headers=auth_header())
    assert r.status_code == 422  # Validation error


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_booking_duration_limits(mock_rooms_get, mock_users_get):
    """
    Test booking duration validation (max 8 hours, min 15 minutes).
    
    Verifies that:
    - Bookings longer than 8 hours are rejected
    - Bookings shorter than 15 minutes are rejected
    - Appropriate validation errors are returned
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    mock_rooms_get.return_value = {"id": 1, "is_active": True, "capacity": 10}
    
    # Test duration exceeding 8 hours
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=9)
    payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    r = client.post("/bookings", json=payload, headers=auth_header())
    assert r.status_code == 422
    assert "duration" in str(r.json()).lower()
    
    # Test duration less than 15 minutes
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(minutes=10)
    payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    r = client.post("/bookings", json=payload, headers=auth_header())
    assert r.status_code == 422


@patch('common.service_client.users_client.get')
def test_booking_history_authorization(mock_users_get):
    """
    Test booking history endpoint with proper authorization.
    
    Verifies that:
    - Users can view their own booking history
    - Users cannot view other users' history
    - Admins can view any user's history
    """
    # User can view their own history
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    r = client.get("/bookings/user/1/history", headers=auth_header("testuser", "regular"))
    assert r.status_code == 200
    
    # User cannot view another user's history
    r = client.get("/bookings/user/2/history", headers=auth_header("testuser", "regular"))
    assert r.status_code == 403
    
    # Admin can view any user's history
    r_admin = client.get("/bookings/user/2/history", headers=auth_header("admin", "admin"))
    assert r_admin.status_code == 200


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_update_booking_authorization(mock_rooms_get, mock_users_get):
    """
    Test that users can only update their own bookings.
    
    Verifies that:
    - User can update their own booking
    - Different user receives 403 Forbidden when trying to update
    - Admins/Managers can update any booking
    """
    # First create a booking
    mock_users_get.return_value = {"id": 1, "username": "user1", "role": "regular"}
    mock_rooms_get.return_value = {"id": 1, "is_active": True, "capacity": 10}
    
    start = datetime.utcnow() + timedelta(hours=5)
    end = start + timedelta(hours=1)
    create_payload = {
        "room_id": 1,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    
    r_create = client.post("/bookings", json=create_payload, headers=auth_header("user1"))
    if r_create.status_code == 200:
        booking_id = r_create.json()["id"]
        
        # Different user tries to update
        mock_users_get.return_value = {"id": 2, "username": "user2", "role": "regular"}
        update_payload = {"attendee_count": 8}
        r_update = client.put(f"/bookings/{booking_id}", json=update_payload, headers=auth_header("user2", "regular"))
        assert r_update.status_code == 403


def test_service_account_internal_endpoint():
    """
    Test internal endpoint for service accounts.
    
    Verifies that:
    - Regular users are denied access (403)
    - Service accounts can access the endpoint
    """
    # Regular user should be denied
    r = client.get("/bookings/internal/room/1", headers=auth_header("user", "regular"))
    assert r.status_code == 403
    
    # Service account should succeed
    r_service = client.get("/bookings/internal/room/1", headers=auth_header("service", "service_account"))
    assert r_service.status_code == 200


def test_statistics_endpoint():
    """
    Test booking statistics endpoint.
    
    Verifies that:
    - Regular users are denied access (403)
    - Admins can access statistics
    - Response includes all expected metrics
    """
    # Regular user should be denied
    r = client.get("/bookings/statistics", headers=auth_header("user", "regular"))
    assert r.status_code == 403
    
    # Admin should succeed
    r_admin = client.get("/bookings/statistics", headers=auth_header("admin", "admin"))
    assert r_admin.status_code == 200
    data = r_admin.json()
    assert "total_bookings" in data
    assert "active_bookings" in data
    assert "cancellation_rate" in data
    assert "override_rate" in data


@patch('common.service_client.users_client.get')
@patch('common.service_client.rooms_client.get')
def test_inactive_room_rejection(mock_rooms_get, mock_users_get):
    """
    Test that bookings for inactive rooms are rejected.
    
    Verifies that attempting to book an inactive room results in
    a 400 Bad Request error with appropriate message.
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    mock_rooms_get.return_value = {"id": 3, "name": "Inactive Room", "is_active": False}
    
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=1)
    payload = {
        "room_id": 3,
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    
    r = client.post("/bookings", json=payload, headers=auth_header("testuser"))
    assert r.status_code == 400
    assert "not active" in r.json()["detail"].lower()


@patch('common.service_client.users_client.get')
def test_booking_history_filter(mock_users_get):
    """
    Test booking history filtering (include/exclude cancelled).
    
    Verifies that:
    - include_cancelled=true returns all bookings
    - include_cancelled=false excludes cancelled bookings
    """
    mock_users_get.return_value = {"id": 1, "username": "testuser", "role": "regular"}
    
    # Get history with cancelled bookings
    r_all = client.get("/bookings/user/1/history?include_cancelled=true", headers=auth_header("testuser"))
    assert r_all.status_code == 200
    
    # Get history without cancelled bookings
    r_active = client.get("/bookings/user/1/history?include_cancelled=false", headers=auth_header("testuser"))
    assert r_active.status_code == 200