"""
Bookings Service API

FastAPI application for managing meeting room bookings, availability checks, and booking history.
Handles booking creation, updates, cancellations, and provides various query endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config
from common.service_client import users_client, rooms_client
from common.error_handlers import setup_error_handlers

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bookings Service",
    description="Service for managing meeting room bookings, availability checks, and booking history",
    version="1.0.0"
)
logging_config.setup_request_logging(app)
setup_error_handlers(app)

def get_db():
    """
    Get database session dependency.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        Automatically closes the session after the request is complete
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_data(token: str = Depends(auth.oauth2_scheme)):
    """
    Decode and return JWT token data.
    
    Args:
        token: JWT token string from Authorization header
        
    Returns:
        dict: Decoded token data containing user information
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    return auth.decode_token(token)

def get_token_string(token: str = Depends(auth.oauth2_scheme)) -> str:
    """
    Get the raw token string for passing to other services.
    
    Args:
        token: JWT token string from Authorization header
        
    Returns:
        str: Raw JWT token string
    """
    return token

@app.get("/health")
def health():
    """
    Health check endpoint.
    
    Returns:
        dict: Status indicating service is running
    """
    return {"status": "ok"}

@app.post("/bookings", response_model=schemas.BookingOut)
def make_booking(booking_in: schemas.BookingCreate, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Create a new booking. User ID is extracted from JWT token.
    
    Args:
        booking_in: Booking details (room_id, start_time, end_time)
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        BookingOut: Created booking
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if user/room not found, 409 if room unavailable
    """
    username = token_data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user_id from users service
    try:
        user_data = users_client.get(f"/users/{username}", token=token)
        user_id = user_data.get("id")
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get user info: {str(e)}")
    
    # Validate room exists
    try:
        room_data = rooms_client.get(f"/rooms/{booking_in.room_id}")
        if not room_data.get("is_active", False):
            raise HTTPException(status_code=400, detail="Room is not active")
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Room not found")
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to validate room: {str(e)}")
    
    # Check availability
    if not crud.is_room_available(db, booking_in.room_id, booking_in.start_time, booking_in.end_time):
        raise HTTPException(status_code=409, detail="Room not available for the requested time")
    
    # Create booking with user_id from token
    return crud.create_booking(db, booking_in, user_id=user_id)

@app.get("/bookings/user/{user_id}", response_model=list[schemas.BookingOut])
def bookings_for_user(user_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Get all bookings for a specific user. Users can view their own bookings, or Admin/Manager/Auditor can view any user's bookings.
    
    Args:
        user_id: ID of the user
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        list[BookingOut]: List of bookings for the user
        
    Raises:
        HTTPException: 403 if not authorized
    """
    username = token_data.get("sub")
    role = token_data.get("role")
    
    # Verify user can access this data (own bookings or admin/auditor/manager)
    if role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR, security.ROLE_MANAGER):
        # Check if this is the user's own bookings
        try:
            user_data = users_client.get(f"/users/{username}", token=token)
            if user_data.get("id") != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to view this user's bookings")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_bookings_for_user(db, user_id)

@app.get("/bookings", response_model=list[schemas.BookingOut])
def list_bookings(db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    List all bookings. Only Admin, Manager, and Auditor roles can access this endpoint.
    
    Args:
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        list[BookingOut]: List of all bookings
        
    Raises:
        HTTPException: 403 if not authorized
    """
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MANAGER, security.ROLE_AUDITOR})
    return crud.list_bookings(db)

@app.get("/bookings/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Get booking by ID.
    
    Args:
        booking_id: ID of the booking
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        BookingOut: Booking details
        
    Raises:
        HTTPException: 404 if booking not found
    """
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.put("/bookings/{booking_id}", response_model=schemas.BookingOut)
def update_booking(booking_id: int, booking_in: schemas.BookingUpdate, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Update a booking. Regular users can update their own bookings.
    Admin and Manager can update any booking.
    
    Args:
        booking_id: ID of the booking to update
        booking_in: Booking update data (room_id, start_time, end_time, status)
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        BookingOut: Updated booking
        
    Raises:
        HTTPException: 403 if not authorized, 404 if booking not found, 409 if room unavailable
    """
    role = token_data.get("role")
    username = token_data.get("sub")
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check authorization: admin/manager can update any, users can update their own
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        # Verify this is the user's own booking
        try:
            user_data = users_client.get(f"/users/{username}", token=token)
            if user_data.get("id") != booking.user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update this booking")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # If updating time, check availability
    if booking_in.start_time or booking_in.end_time:
        new_start = booking_in.start_time if booking_in.start_time else booking.start_time
        new_end = booking_in.end_time if booking_in.end_time else booking.end_time
        
        # Check if the new time slot is available (excluding current booking)
        # Get all bookings for this room in the time range
        from sqlalchemy import and_
        overlapping = db.query(models.Booking).filter(
            models.Booking.room_id == booking.room_id,
            models.Booking.id != booking_id,
            models.Booking.status == "booked",
            and_(
                models.Booking.start_time < new_end,
                models.Booking.end_time > new_start
            )
        ).count()
        
        if overlapping > 0:
            raise HTTPException(status_code=409, detail="Room not available for the requested time")
    
    booking = crud.update_booking(db, booking_id, booking_in)
    return booking

@app.post("/bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Cancel a booking. Users can cancel their own bookings, or Admin/Manager can cancel any booking.
    
    Args:
        booking_id: ID of the booking to cancel
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        BookingOut: Cancelled booking
        
    Raises:
        HTTPException: 403 if not authorized, 404 if booking not found
    """
    role = token_data.get("role")
    username = token_data.get("sub")
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check authorization: admin/manager can cancel any, users can cancel their own
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        # Verify this is the user's own booking
        try:
            user_data = users_client.get(f"/users/{username}", token=token)
            if user_data.get("id") != booking.user_id:
                raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    booking = crud.cancel_booking(db, booking_id)
    return booking

@app.get("/bookings/availability/{room_id}", response_model=dict)
def check_availability(room_id: int, start_time: str, end_time: str, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Check if a room is available for a specific time slot.
    
    Args:
        room_id: ID of the room to check
        start_time: Start time in ISO format (e.g., "2025-01-15T10:00:00")
        end_time: End time in ISO format (e.g., "2025-01-15T11:00:00")
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        dict: Availability status with room_id and available flag
        
    Raises:
        HTTPException: 400 if datetime format is invalid or end_time <= start_time
    """
    from datetime import datetime
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    available = crud.is_room_available(db, room_id, start, end)
    return {"room_id": room_id, "available": available, "start_time": start_time, "end_time": end_time}

@app.get("/bookings/user/{user_id}/history")
def get_booking_history(
    user_id: int, 
    include_cancelled: bool = True,
    db: Session = Depends(get_db),
    token_data = Depends(get_token_data)
):
    """
    Get complete booking history for a user.
    
    Args:
        user_id: ID of the user
        include_cancelled: Whether to include cancelled bookings (default: True)
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        list: List of bookings ordered by creation date (descending)
    """
    # Authorization check...
    query = db.query(models.Booking).filter(
        models.Booking.user_id == user_id
    )
    if not include_cancelled:
        query = query.filter(models.Booking.status == "booked")
    return query.order_by(models.Booking.created_at.desc()).all()

@app.get("/bookings/internal/room/{room_id}")
def get_room_bookings_internal(
    room_id: int, 
    db: Session = Depends(get_db),
    token_data = Depends(get_token_data)
):
    """
    Internal endpoint for service-to-service communication.
    Get all bookings for a specific room. Requires service account role.
    
    Args:
        room_id: ID of the room
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        list: List of bookings for the room
        
    Raises:
        HTTPException: 403 if not a service account
    """
    security.require_role(token_data, security.ROLE_SERVICE_ACCOUNT)
    return crud.get_bookings_for_room(db, room_id)

@app.get("/bookings/statistics")
def get_statistics(
    db: Session = Depends(get_db),
    token_data = Depends(get_token_data)
):
    """
    Get booking statistics - Admin only.
    
    Args:
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        dict: Statistics including total bookings, active bookings, 
              cancelled bookings, cancellation rate, and override rate
              
    Raises:
        HTTPException: 403 if not admin
    """
    security.require_role(token_data, security.ROLE_ADMIN)
    stats = crud.get_booking_statistics(db)
    
    # Calculate override rate
    total = stats["total_bookings"]
    overridden = db.query(models.Booking).filter(
        models.Booking.status == "overridden"
    ).count()
    
    stats["override_rate"] = (overridden / total * 100) if total > 0 else 0
    return stats


@app.post("/bookings/{booking_id}/override", response_model=schemas.BookingOut)
def override_booking(
    booking_id: int,
    reason: str,
    db: Session = Depends(get_db),
    token_data = Depends(get_token_data)
):
    """
    Override a booking - Admin/Manager only.
    Sets the booking status to 'overridden' with a reason.
    
    Args:
        booking_id: ID of the booking to override
        reason: Reason for overriding the booking
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        BookingOut: Overridden booking with updated status
        
    Raises:
        HTTPException: 403 if not admin/manager, 404 if booking not found
    """
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MANAGER})
    
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = "overridden"
    booking.override_reason = reason
    db.commit()
    db.refresh(booking)
    return booking