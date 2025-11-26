from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from . import models, schemas


def is_room_available(db: Session, room_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: int = None) -> bool:
    """
    Check if a room is available for a specific time slot.
    
    Args:
        db: Database session
        room_id: ID of the room to check
        start_time: Start time of the booking
        end_time: End time of the booking
        exclude_booking_id: Optional booking ID to exclude (for updates)
    
    Returns:
        bool: True if room is available, False otherwise
    """
    query = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.status == "booked",
        and_(
            models.Booking.start_time < end_time,
            models.Booking.end_time > start_time
        )
    )
    
    # Exclude specific booking when updating
    if exclude_booking_id:
        query = query.filter(models.Booking.id != exclude_booking_id)
    
    return query.count() == 0


def get_conflicting_bookings(db: Session, room_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: int = None) -> list:
    """
    Get list of conflicting booking IDs for a time slot.
    
    Args:
        db: Database session
        room_id: ID of the room to check
        start_time: Start time of the booking
        end_time: End time of the booking
        exclude_booking_id: Optional booking ID to exclude (for updates)
    
    Returns:
        list: List of conflicting booking IDs
    """
    query = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.status == "booked",
        and_(
            models.Booking.start_time < end_time,
            models.Booking.end_time > start_time
        )
    )
    
    if exclude_booking_id:
        query = query.filter(models.Booking.id != exclude_booking_id)
    
    return [b.id for b in query.all()]


def create_booking(db: Session, booking_in: schemas.BookingCreate, user_id: int) -> models.Booking:
    """
    Create a new booking.
    
    Args:
        db: Database session
        booking_in: Booking creation schema with room_id, start_time, and end_time
        user_id: ID of the user making the booking
    
    Returns:
        models.Booking: The newly created booking object
    """
    booking = models.Booking(
        user_id=user_id,
        room_id=booking_in.room_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        status="booked"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking(db: Session, booking_id: int) -> models.Booking | None:
    """
    Get booking by ID.
    
    Args:
        db: Database session
        booking_id: ID of the booking to retrieve
    
    Returns:
        models.Booking | None: Booking object if found, None otherwise
    """
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def get_bookings_for_user(db: Session, user_id: int, include_cancelled: bool = True) -> list[models.Booking]:
    """
    Get all bookings for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        include_cancelled: Whether to include cancelled bookings (default: True)
    
    Returns:
        list[models.Booking]: List of bookings ordered by start time (descending)
    """
    query = db.query(models.Booking).filter(models.Booking.user_id == user_id)
    
    if not include_cancelled:
        query = query.filter(models.Booking.status == "booked")
    
    return query.order_by(models.Booking.start_time.desc()).all()


def get_bookings_for_room(db: Session, room_id: int, status: str = None) -> list[models.Booking]:
    """
    Get all bookings for a specific room.
    
    Args:
        db: Database session
        room_id: ID of the room
        status: Optional status filter ('booked' or 'cancelled')
    
    Returns:
        list[models.Booking]: List of bookings ordered by start time (descending)
    """
    query = db.query(models.Booking).filter(models.Booking.room_id == room_id)
    
    if status:
        query = query.filter(models.Booking.status == status)
    
    return query.order_by(models.Booking.start_time.desc()).all()


def list_bookings(db: Session, status: str = None, limit: int = None) -> list[models.Booking]:
    """
    List all bookings with optional filtering.
    
    Args:
        db: Database session
        status: Optional status filter ('booked' or 'cancelled')
        limit: Optional maximum number of results to return
    
    Returns:
        list[models.Booking]: List of bookings ordered by start time (descending)
    """
    query = db.query(models.Booking)
    
    if status:
        query = query.filter(models.Booking.status == status)
    
    query = query.order_by(models.Booking.start_time.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def update_booking(db: Session, booking_id: int, booking_in: schemas.BookingUpdate) -> models.Booking | None:
    """
    Update an existing booking.
    
    Args:
        db: Database session
        booking_id: ID of the booking to update
        booking_in: Booking update schema with fields to update
    
    Returns:
        models.Booking | None: Updated booking object if found, None otherwise
    """
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    
    # Update only provided fields
    data = booking_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(db: Session, booking_id: int) -> models.Booking | None:
    """
    Cancel a booking by setting status to 'cancelled'.
    
    Args:
        db: Database session
        booking_id: ID of the booking to cancel
    
    Returns:
        models.Booking | None: Cancelled booking object if found, None otherwise
    """
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking


def delete_booking(db: Session, booking_id: int) -> bool:
    """
    Hard delete a booking (use with caution).
    
    Args:
        db: Database session
        booking_id: ID of the booking to delete
    
    Returns:
        bool: True if booking was deleted, False if not found
    """
    booking = get_booking(db, booking_id)
    if not booking:
        return False
    
    db.delete(booking)
    db.commit()
    return True


def get_upcoming_bookings(db: Session, user_id: int = None, room_id: int = None) -> list[models.Booking]:
    """
    Get upcoming (future) bookings.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        room_id: Optional room ID to filter by
    
    Returns:
        list[models.Booking]: List of future bookings ordered by start time (ascending)
    """
    now = datetime.utcnow()
    query = db.query(models.Booking).filter(
        models.Booking.start_time > now,
        models.Booking.status == "booked"
    )
    
    if user_id:
        query = query.filter(models.Booking.user_id == user_id)
    
    if room_id:
        query = query.filter(models.Booking.room_id == room_id)
    
    return query.order_by(models.Booking.start_time).all()


def get_booking_statistics(db: Session) -> dict:
    """
    Get booking statistics for analytics.
    
    Args:
        db: Database session
    
    Returns:
        dict: Dictionary containing:
            - total_bookings: Total number of bookings
            - active_bookings: Number of active bookings
            - cancelled_bookings: Number of cancelled bookings
            - cancellation_rate: Percentage of cancelled bookings
    """
    total = db.query(models.Booking).count()
    active = db.query(models.Booking).filter(models.Booking.status == "booked").count()
    cancelled = db.query(models.Booking).filter(models.Booking.status == "cancelled").count()
    
    return {
        "total_bookings": total,
        "active_bookings": active,
        "cancelled_bookings": cancelled,
        "cancellation_rate": (cancelled / total * 100) if total > 0 else 0
    }