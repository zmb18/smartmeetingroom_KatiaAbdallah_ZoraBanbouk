from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import root_validator, validator

class BookingCreate(BaseModel):
    """Schema for creating a new booking. user_id is extracted from JWT token."""
    room_id: int = Field(..., gt=0, description="ID of the room to book")
    start_time: datetime = Field(..., description="Booking start time (ISO format)")
    end_time: datetime = Field(..., description="Booking end time (ISO format)")

    @root_validator
    def validate_times(cls, values):
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end:
            if end <= start:
                raise ValueError("end_time must be after start_time")
            # Check if booking is in the future
            from datetime import datetime as dt
            if start < dt.now():
                raise ValueError("start_time must be in the future")
        return values

class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    start_time: datetime | None = Field(None, description="New start time (ISO format)")
    end_time: datetime | None = Field(None, description="New end time (ISO format)")
    status: str | None = Field(None, max_length=32, description="Booking status")

    @root_validator
    def validate_times(cls, values):
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end and end <= start:
            raise ValueError("end_time must be after start_time")
        return values
    
    @validator('status')
    def validate_status(cls, v):
        if v is None:
            return v
        valid_statuses = ['booked', 'cancelled', 'completed', 'overridden']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

class BookingOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    status: str

    class Config:
        orm_mode = True
