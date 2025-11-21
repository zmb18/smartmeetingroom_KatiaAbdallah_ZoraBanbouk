from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import root_validator, Field

class BookingCreate(BaseModel):
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime

    @root_validator
    def validate_times(cls, values):
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end and end <= start:
            raise ValueError("end_time must be after start_time")
        return values

class BookingUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = Field(None, max_length=32)

    @root_validator
    def validate_times(cls, values):
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end and end <= start:
            raise ValueError("end_time must be after start_time")
        return values

class BookingOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    status: str

    class Config:
        orm_mode = True
