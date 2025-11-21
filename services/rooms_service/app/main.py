from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rooms Service")
logging_config.setup_request_logging(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_role(token: str = Depends(auth.oauth2_scheme)):
    payload = auth.decode_token(token)
    return payload.get("role", "regular")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/rooms", response_model=schemas.RoomOut)
def create_room(room_in: schemas.RoomCreate, db: Session = Depends(get_db), role: str = Depends(get_current_role)):
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.create_room(db, room_in)

@app.get("/rooms/{room_id}", response_model=schemas.RoomOut)
def read_room(room_id: int, db: Session = Depends(get_db)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.get("/rooms", response_model=list[schemas.RoomOut])
def list_rooms(capacity: int | None = None, location: str | None = None, equipment: str | None = None, db: Session = Depends(get_db)):
    equipment_list = None
    if equipment:
        equipment_list = [e.strip() for e in equipment.split(",")]
    return crud.search_rooms(db, capacity=capacity, location=location, equipment=equipment_list)

@app.put("/rooms/{room_id}", response_model=schemas.RoomOut)
def update_room(room_id: int, room_in: schemas.RoomUpdate, db: Session = Depends(get_db), role: str = Depends(get_current_role)):
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized")
    room = crud.update_room(db, room_id, room_in)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: int, db: Session = Depends(get_db), role: str = Depends(get_current_role)):
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized")
    ok = crud.delete_room(db, room_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Room not found")
    return None

@app.get("/rooms/{room_id}/availability", response_model=dict)
def room_availability(room_id: int, db: Session = Depends(get_db)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"room_id": room_id, "is_active": room.is_active}
