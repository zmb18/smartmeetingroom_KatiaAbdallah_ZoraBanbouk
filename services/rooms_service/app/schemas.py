from pydantic import BaseModel, Field
from typing import Optional, List

class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., ge=1, le=10000)
    equipment: Optional[List[str]] = []
    location: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = True

class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=10000)
    equipment: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class RoomOut(BaseModel):
    id: int
    name: str
    capacity: int
    equipment: Optional[List[str]]
    location: Optional[str]
    is_active: bool

    class Config:
        orm_mode = True
