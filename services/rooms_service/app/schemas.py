from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class RoomCreate(BaseModel):
    """Schema for creating a new room."""
    name: str = Field(..., min_length=1, max_length=100, description="Room name (must be unique)")
    capacity: int = Field(..., ge=1, le=10000, description="Room capacity (1-10000)")
    equipment: Optional[List[str]] = Field(default=[], description="List of available equipment")
    location: Optional[str] = Field(None, max_length=255, description="Room location")
    is_active: Optional[bool] = Field(True, description="Whether room is active")
    
    @validator('equipment')
    def validate_equipment(cls, v):
        """
        Validate and sanitize equipment list:
        - Remove empty strings
        - Remove duplicates (case-insensitive)
        - Trim whitespace
        """
        if v is None:
            return []
        # Remove empty and whitespace-only items, and trim
        cleaned = [item.strip() for item in v if item and item.strip()]
        # Remove duplicates while preserving order (case-insensitive)
        seen = set()
        result = []
        for item in cleaned:
            if item.lower() not in seen:
                seen.add(item.lower())
                result.append(item)
        return result
    
    @validator('name')
    def validate_name(cls, v):
        """Validate room name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Room name cannot be empty or whitespace")
        return v.strip()

class RoomUpdate(BaseModel):
    """Schema for updating an existing room."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated room name")
    capacity: Optional[int] = Field(None, ge=1, le=10000, description="Updated capacity")
    equipment: Optional[List[str]] = Field(None, description="Updated equipment list")
    location: Optional[str] = Field(None, max_length=255, description="Updated location")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    
    @validator('equipment')
    def validate_equipment(cls, v):
        """Validate and sanitize equipment list"""
        if v is None:
            return None
        # Remove empty and whitespace-only items, and trim
        cleaned = [item.strip() for item in v if item and item.strip()]
        # Remove duplicates while preserving order (case-insensitive)
        seen = set()
        result = []
        for item in cleaned:
            if item.lower() not in seen:
                seen.add(item.lower())
                result.append(item)
        return result
    
    @validator('name')
    def validate_name(cls, v):
        """Validate room name is not just whitespace"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Room name cannot be empty or whitespace")
        return v.strip() if v else None

class RoomOut(BaseModel):
    """Schema for room output."""
    id: int
    name: str
    capacity: int
    equipment: Optional[List[str]]
    location: Optional[str]
    is_active: bool
    created_at: datetime  # ✅ ADDED
    updated_at: datetime  # ✅ ADDED

    class Config:
        orm_mode = True