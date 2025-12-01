"""
Fixed Bookings Service main.py with proper token forwarding
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config
from common.service_client import users_client, rooms_client
from common.error_handlers import setup_error_handlers
from datetime import datetime
from typing import Optional

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bookings Service",
    description="Service for managing meeting room bookings",
    version="1.0.0"
)
logging_config.setup_request_logging(app)
setup_error_handlers(app)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_token_data(token: str = Depends(auth.oauth2_scheme)):
    """Decode and return full token payload"""
    return auth.decode_token(token)


def get_token_string(token: str = Depends(auth.oauth2_scheme)) -> str:
    """Get the raw token string for passing to other services"""
    return token


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/bookings", response_model=schemas.BookingOut)
def create_booking(
    booking_in: schemas.BookingCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data),
    token: str = Depends(get_token_string) 
):
    """
    Create a new booking.
    
    Steps:
    1. Extract user_id from JWT token
    2. Verify user exists
    3. Verify room exists and is active
    4. Check room availability
    5. Validate capacity if attendee_count provided
    6. Create booking
    """
    username = token_data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
   
    try:
        user_data = users_client.get(
            f"/users/{username}",
            token=token  
        )
        user_id = user_data["id"]
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=503, detail="Users service unavailable")
    

    try:
        room_data = rooms_client.get(
            f"/rooms/{booking_in.room_id}",
            token=token  
        )
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Room not found")
        elif e.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized to access rooms service")
        raise HTTPException(status_code=503, detail="Rooms service unavailable")
    
   
    if not room_data.get("is_active"):
        raise HTTPException(status_code=400, detail="Room is not active")

    if booking_in.attendee_count:
        room_capacity = room_data.get("capacity")
        if room_capacity and booking_in.attendee_count > room_capacity:
            raise HTTPException(
                status_code=400,
                detail=f"Attendee count ({booking_in.attendee_count}) exceeds room capacity ({room_capacity})"
            )
    
   
    if not crud.is_room_available(
        db, booking_in.room_id, booking_in.start_time, booking_in.end_time
    ):
        conflicting = crud.get_conflicting_bookings(
            db, booking_in.room_id, booking_in.start_time, booking_in.end_time
        )
        raise HTTPException(
            status_code=409,
            detail=f"Room not available for the requested time. Conflicting bookings: {conflicting}"
        )
    
    
    booking = crud.create_booking(db, booking_in, user_id)
    return booking


@app.get("/bookings/{booking_id}", response_model=schemas.BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """Get a specific booking by ID."""
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.get("/bookings/user/{user_id}/history", response_model=list[schemas.BookingOut])
def get_user_bookings(
    user_id: int,
    include_cancelled: bool = True,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data),
    token: str = Depends(get_token_string)
):
    """
    Get all bookings for a specific user.
    
    Authorization:
    - Users can view their own bookings
    - Admins/Managers can view any user's bookings
    """
    username = token_data.get("sub")
    role = token_data.get("role", "regular")
    
   
    try:
        current_user = users_client.get(
            f"/users/{username}",
            token=token  
        )
        current_user_id = current_user["id"]
    except:
        raise HTTPException(status_code=503, detail="Users service unavailable")
    
  
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER, security.ROLE_AUDITOR):
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view other users' bookings")
    
    return crud.get_bookings_for_user(db, user_id, include_cancelled)


@app.get("/bookings/room/{room_id}", response_model=list[schemas.BookingOut])
def get_room_bookings(
    room_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """Get all bookings for a specific room."""
    return crud.get_bookings_for_room(db, room_id, status)


@app.get("/bookings", response_model=list[schemas.BookingOut])
def list_bookings(
    status: Optional[str] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """List all bookings with optional filtering."""
    return crud.list_bookings(db, status, limit)


@app.put("/bookings/{booking_id}", response_model=schemas.BookingOut)
def update_booking(
    booking_id: int,
    booking_in: schemas.BookingUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data),
    token: str = Depends(get_token_string)
):
    """
    Update a booking.
    
    Authorization:
    - Users can update their own bookings
    - Admins/Managers can update any booking
    """
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    username = token_data.get("sub")
    role = token_data.get("role", "regular")
    
   
    try:
        current_user = users_client.get(
            f"/users/{username}",
            token=token  
        )
        current_user_id = current_user["id"]
    except:
        raise HTTPException(status_code=503, detail="Users service unavailable")
    
  
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        if booking.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this booking")
    

    if booking_in.start_time and booking_in.end_time:
        if not crud.is_room_available(
            db, booking.room_id, booking_in.start_time, booking_in.end_time, exclude_booking_id=booking_id
        ):
            raise HTTPException(status_code=409, detail="Room not available for the requested time")
    
    updated_booking = crud.update_booking(db, booking_id, booking_in)
    return updated_booking


@app.post("/bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(
    booking_id: int,
    cancellation: schemas.CancellationRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data),
    token: str = Depends(get_token_string)
):
    """
    Cancel a booking.
    
    Authorization:
    - Users can cancel their own bookings
    - Admins/Managers can cancel any booking
    """
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    username = token_data.get("sub")
    role = token_data.get("role", "regular")
    
    
    try:
        current_user = users_client.get(
            f"/users/{username}",
            token=token 
        )
        current_user_id = current_user["id"]
    except:
        raise HTTPException(status_code=503, detail="Users service unavailable")
    
  
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        if booking.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
    
   
    if cancellation.reason:
        booking.cancellation_reason = cancellation.reason
    
    cancelled_booking = crud.cancel_booking(db, booking_id)
    return cancelled_booking


@app.post("/bookings/{booking_id}/override", response_model=schemas.BookingOut)
def override_booking(
    booking_id: int,
    override: schemas.OverrideRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """
    Override a booking (Admin/Manager only).
    
    This forces cancellation regardless of booking owner.
    """
    role = token_data.get("role", "regular")
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Only admins and managers can override bookings")
    
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = "overridden"
    booking.override_reason = override.reason
    db.commit()
    db.refresh(booking)
    return booking


@app.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """
    Hard delete a booking (Admin only).
    """
    role = token_data.get("role", "regular")
    if role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete bookings")
    
    if not crud.delete_booking(db, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return None


@app.get("/bookings/availability/{room_id}", response_model=schemas.AvailabilityCheck)
def check_availability(
    room_id: int,
    start_time: str,
    end_time: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """
    Check if a room is available for a specific time slot.
    """
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
    
    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    
    available = crud.is_room_available(db, room_id, start, end)
    conflicting = [] if available else crud.get_conflicting_bookings(db, room_id, start, end)
    
    return schemas.AvailabilityCheck(
        room_id=room_id,
        available=available,
        start_time=start_time,
        end_time=end_time,
        conflicting_bookings=conflicting
    )


@app.get("/bookings/internal/room/{room_id}", response_model=list[schemas.BookingOut])
def get_room_bookings_internal(
    room_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """
    Internal endpoint for service accounts to get room bookings.
    """
    role = token_data.get("role", "regular")
    if role != security.ROLE_SERVICE_ACCOUNT:
        raise HTTPException(status_code=403, detail="Service account role required")
    
    return crud.get_bookings_for_room(db, room_id, status="booked")


@app.get("/bookings/statistics")
def get_statistics(
    db: Session = Depends(get_db),
    token_data: dict = Depends(get_token_data)
):
    """
    Get booking statistics (Admin/Manager/Auditor only).
    """
    role = token_data.get("role", "regular")
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    stats = crud.get_booking_statistics(db)
    
   
    total = stats["total_bookings"]
    overridden = db.query(models.Booking).filter(models.Booking.status == "overridden").count()
    stats["override_rate"] = (overridden / total * 100) if total > 0 else 0
    
    return stats
