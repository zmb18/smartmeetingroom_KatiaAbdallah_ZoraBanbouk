from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config
from common.service_client import bookings_client
from common.error_handlers import setup_error_handlers
from datetime import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rooms Service",
    description="Service for managing meeting rooms, room availability, and room details",
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

def get_current_role(token: str = Depends(auth.oauth2_scheme)):
    """Helper to get just the role (for backward compatibility)"""
    payload = auth.decode_token(token)
    return payload.get("role", "regular")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/rooms", response_model=schemas.RoomOut)
def create_room(room_in: schemas.RoomCreate, db: Session = Depends(get_db), 
                token_data = Depends(get_token_data)):
    """
    Create a new meeting room. Only Admin and Facility Manager roles can create rooms.
    
    Args:
        room_in: Room details (name, capacity, equipment, location, is_active)
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        RoomOut: Created room
        
    Raises:
        HTTPException: 403 if not authorized (requires Admin or Manager role)
    """
    role = token_data.get("role")
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized. Admin or Facility Manager role required.")
    return crud.create_room(db, room_in)

@app.get("/rooms/{room_id}", response_model=schemas.RoomOut)
def read_room(room_id: int, db: Session = Depends(get_db), 
              token_data = Depends(get_token_data)):
    """
    Get details of a specific room. All authenticated users can view room details.
    
    Args:
        room_id: ID of the room
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        RoomOut: Room details
        
    Raises:
        HTTPException: 404 if room not found
    """
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.get("/rooms", response_model=list[schemas.RoomOut])
def list_rooms(capacity: int | None = None, location: str | None = None, 
               equipment: str | None = None, db: Session = Depends(get_db),
               token_data = Depends(get_token_data)):
    """
    List and filter rooms. All authenticated users can search rooms.
    
    Args:
        capacity: Minimum capacity required (optional)
        location: Filter by exact location match (optional)
        equipment: Comma-separated list of required equipment (optional)
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        list[RoomOut]: List of rooms matching the criteria
        
    Examples:
        GET /rooms?capacity=10
        GET /rooms?location=1st floor
        GET /rooms?equipment=projector,whiteboard
        GET /rooms?capacity=20&location=2nd floor&equipment=projector
    """
    equipment_list = None
    if equipment:
        equipment_list = [e.strip() for e in equipment.split(",")]
    return crud.search_rooms(db, capacity=capacity, location=location, equipment=equipment_list)

@app.put("/rooms/{room_id}", response_model=schemas.RoomOut)
def update_room(room_id: int, room_in: schemas.RoomUpdate, 
                db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Update room details. Only Admin and Facility Manager roles can update rooms.
    
    Args:
        room_id: ID of the room to update
        room_in: Updated room data (name, capacity, equipment, location, is_active)
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        RoomOut: Updated room
        
    Raises:
        HTTPException: 403 if not authorized, 404 if room not found
    """
    role = token_data.get("role")
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized. Admin or Facility Manager role required.")
    room = crud.update_room(db, room_id, room_in)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: int, db: Session = Depends(get_db), 
                token_data = Depends(get_token_data)):
    """
    Delete a room. Only Admin and Facility Manager roles can delete rooms.
    
    Args:
        room_id: ID of the room to delete
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: 403 if not authorized, 404 if room not found
    """
    role = token_data.get("role")
    if role not in (security.ROLE_ADMIN, security.ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized. Admin or Facility Manager role required.")
    ok = crud.delete_room(db, room_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Room not found")
    return None

@app.get("/rooms/{room_id}/availability", response_model=dict)
def room_availability(room_id: int, start_time: str = None, end_time: str = None, 
                      db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Check room availability. All authenticated users can check availability.
    
    If start_time and end_time are provided, checks if room is available for that specific time slot
    by querying the bookings service. Otherwise, returns general room status (active/inactive).
    
    Args:
        room_id: ID of the room
        start_time: Start time in ISO format (e.g., "2025-01-15T10:00:00") - optional
        end_time: End time in ISO format (e.g., "2025-01-15T11:00:00") - optional
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        dict: Availability status including:
            - room_id: ID of the room
            - is_active: Whether room is active
            - available: Whether room is available (considers both is_active and bookings)
            - checked_time_slot: Time slot checked (if provided)
            - note: Additional information (if applicable)
        
    Raises:
        HTTPException: 404 if room not found, 400 if datetime format invalid
        
    Examples:
        GET /rooms/1/availability
        GET /rooms/1/availability?start_time=2025-01-15T10:00:00&end_time=2025-01-15T11:00:00
    """
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    result = {
        "room_id": room_id,
        "is_active": room.is_active,
        "available": room.is_active  # Default to is_active if no time check
    }
    
    # If time parameters provided, check actual booking availability
    if start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            if end <= start:
                raise HTTPException(status_code=400, detail="end_time must be after start_time")
            
            # Call bookings service to check availability
            try:
                availability_data = bookings_client.get(
                    f"/bookings/availability/{room_id}",
                    params={"start_time": start_time, "end_time": end_time}
                )
                result["available"] = availability_data.get("available", False) and room.is_active
                result["checked_time_slot"] = {
                    "start_time": start_time,
                    "end_time": end_time
                }
            except HTTPException as e:
                # If bookings service returns specific error, propagate it
                if e.status_code != 503:
                    raise
                # If bookings service unavailable, fall back to is_active
                result["available"] = room.is_active
                result["note"] = "Could not verify booking availability - bookings service unavailable"
            except Exception as e:
                # Generic error handling
                result["available"] = room.is_active
                result["note"] = f"Could not verify booking availability: {str(e)}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
    
    return result

@app.get("/rooms/{room_id}/status", response_model=dict)
def room_status(room_id: int, db: Session = Depends(get_db), 
                token_data = Depends(get_token_data)):
    """
    Get detailed room status. Admin, Manager, and Auditor can access full details.
    Regular users get basic status only.
    
    Args:
        room_id: ID of the room
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        dict: Room status including:
            - Basic room details (name, capacity, equipment, location)
            - is_active status
            - Current bookings count (if authorized)
            
    Raises:
        HTTPException: 404 if room not found
    """
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    role = token_data.get("role")
    
    status = {
        "room_id": room_id,
        "name": room.name,
        "is_active": room.is_active,
        "capacity": room.capacity,
        "equipment": room.equipment,
        "location": room.location
    }
    
    # Admin, Manager, and Auditor can see booking information
    if role in (security.ROLE_ADMIN, security.ROLE_MANAGER, security.ROLE_AUDITOR):
        try:
            # Get bookings for this room
            from datetime import datetime, timedelta
            now = datetime.now().isoformat()
            future = (datetime.now() + timedelta(days=30)).isoformat()
            
            # Note: This assumes bookings service has an endpoint to filter by room
            # If not available, this would need to be adjusted
            status["note"] = "Booking details require bookings service integration"
        except Exception as e:
            status["bookings_error"] = f"Could not fetch booking information: {str(e)}"
    
    return status