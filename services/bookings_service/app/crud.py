from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas

def is_room_available(db: Session, room_id: int, start_time, end_time):
    # returns True if no existing booking overlaps
    q = db.query(models.Booking).filter(models.Booking.room_id == room_id, models.Booking.status == "booked",
        and_(models.Booking.start_time < end_time, models.Booking.end_time > start_time))
    return q.count() == 0

def create_booking(db: Session, booking_in: schemas.BookingCreate, user_id: int):
    booking = models.Booking(user_id=user_id, room_id=booking_in.room_id, start_time=booking_in.start_time, end_time=booking_in.end_time)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

def get_booking(db: Session, booking_id: int):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()

def get_bookings_for_user(db: Session, user_id: int):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).all()

def list_bookings(db: Session):
    return db.query(models.Booking).all()

def update_booking(db: Session, booking_id: int, booking_in: schemas.BookingUpdate):
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    data = booking_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(booking, field, value)
    db.commit()
    db.refresh(booking)
    return booking

def cancel_booking(db: Session, booking_id: int):
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking
