from sqlalchemy.orm import Session
from . import models, schemas

def create_room(db: Session, room_in: schemas.RoomCreate):
    room = models.Room(name=room_in.name, capacity=room_in.capacity, equipment=room_in.equipment, location=room_in.location, is_active=room_in.is_active)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def get_room(db: Session, room_id: int):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def update_room(db: Session, room_id: int, room_in: schemas.RoomUpdate):
    room = get_room(db, room_id)
    if not room:
        return None
    data = room_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(room, field, value)
    db.commit()
    db.refresh(room)
    return room

def delete_room(db: Session, room_id: int):
    room = get_room(db, room_id)
    if not room:
        return False
    db.delete(room)
    db.commit()
    return True

def search_rooms(db: Session, capacity: int | None = None, location: str | None = None, equipment: list | None = None):
    q = db.query(models.Room).filter(models.Room.is_active == True)
    if capacity:
        q = q.filter(models.Room.capacity >= capacity)
    if location:
        q = q.filter(models.Room.location == location)
    
    rooms = q.all()
    
    # Filter by equipment in Python (more reliable for JSON arrays)
    if equipment:
        filtered_rooms = []
        for room in rooms:
            room_equipment = room.equipment if room.equipment else []
            # Check if all requested equipment items are in room's equipment
            if all(eq_item in room_equipment for eq_item in equipment):
                filtered_rooms.append(room)
        return filtered_rooms
    
    return rooms
