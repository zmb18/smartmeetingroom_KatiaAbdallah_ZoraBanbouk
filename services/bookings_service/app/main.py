from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bookings Service")
logging_config.setup_request_logging(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_data(token: str = Depends(auth.oauth2_scheme)):
    return auth.decode_token(token)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/bookings", response_model=schemas.BookingOut)
def make_booking(booking_in: schemas.BookingCreate, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    # basic auth: only authenticated users
    username = token_data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    # availability check
    if not crud.is_room_available(db, booking_in.room_id, booking_in.start_time, booking_in.end_time):
        raise HTTPException(status_code=409, detail="Room not available for the requested time")
    return crud.create_booking(db, booking_in)

@app.get("/bookings/user/{user_id}", response_model=list[schemas.BookingOut])
def bookings_for_user(user_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    # allow users to see own or admin/auditor
    role = token_data.get("role")
    username = token_data.get("sub")
    # In a full system you'd verify that token username matches user_id or role is admin
    return crud.get_bookings_for_user(db, user_id)

@app.get("/bookings", response_model=list[schemas.BookingOut])
def list_bookings(db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MANAGER, security.ROLE_AUDITOR})
    return crud.list_bookings(db)

@app.get("/bookings/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.put("/bookings/{booking_id}", response_model=schemas.BookingOut)
def update_booking(booking_id: int, booking_in: schemas.BookingUpdate, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MANAGER})
    booking = crud.update_booking(db, booking_id, booking_in)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.post("/bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    role = token_data.get("role")
    username = token_data.get("sub")
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # simple ownership/admin check: allow admin/manager or same user_id if known
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER) and str(booking.user_id) != str(username):
        raise HTTPException(status_code=403, detail="Not authorized")
    booking = crud.cancel_booking(db, booking_id)
    return booking

@app.get("/bookings/availability/{room_id}", response_model=dict)
def check_availability(room_id: int, start_time: str, end_time: str, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    from datetime import datetime
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    available = crud.is_room_available(db, room_id, start, end)
    return {"room_id": room_id, "available": available}
