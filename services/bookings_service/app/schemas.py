"""
Pydantic schemas for the Bookings service.

This module defines the request and response schemas for booking operations,
including validation rules for booking times, durations, and status values.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import root_validator, validator
import os

class BookingCreate(BaseModel):
    """
    Schema for creating a new booking. user_id is extracted from JWT token.
    
    Attributes:
        room_id: ID of the room to book (must be positive)
        start_time: Booking start time in ISO format
        end_time: Booking end time in ISO format
        
    Validation:
        - end_time must be after start_time
        - start_time must be in the future (in production)
        - Booking duration must be at least 15 minutes
        - Booking duration cannot exceed 8 hours
    """
    room_id: int = Field(..., gt=0, description="ID of the room to book")
    start_time: datetime = Field(..., description="Booking start time (ISO format)")
    end_time: datetime = Field(..., description="Booking end time (ISO format)")
    attendee_count: int | None = Field(None, description="Number of attendees")

    @root_validator
    def validate_times(cls, values):
        """
        Validate that end_time is after start_time and start_time is in the future.
        
        Args:
            values: Dictionary of field values
            
        Returns:
            dict: Validated values
            
        Raises:
            ValueError: If end_time <= start_time or start_time is in the past
        """
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end:
            if end <= start:
                raise ValueError("end_time must be after start_time")
            
            # Only validate future time in production (not in tests)
            if os.getenv("TESTING") != "true":
                from datetime import datetime as dt
                if start < dt.now():
                    raise ValueError("start_time must be in the future")
        return values
    
    @root_validator
    def validate_duration(cls, values):
        """
        Validate that booking duration is between 15 minutes and 8 hours.
        
        Args:
            values: Dictionary of field values
            
        Returns:
            dict: Validated values
            
        Raises:
            ValueError: If duration is less than 15 minutes or more than 8 hours
        """
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end:
            duration = (end - start).total_seconds() / 3600
            if duration < 0.25:  # 15 minutes
                raise ValueError("Booking must be at least 15 minutes")
            if duration > 8:
                raise ValueError("Booking cannot exceed 8 hours")
        return values

class BookingUpdate(BaseModel):
    """
    Schema for updating a booking.
    
    Attributes:
        start_time: Optional new start time in ISO format
        end_time: Optional new end time in ISO format
        status: Optional new booking status (booked, cancelled, completed, overridden)
        
    Validation:
        - If both times provided, end_time must be after start_time
        - Status must be one of the valid status values
    """
    start_time: datetime | None = Field(None, description="New start time (ISO format)")
    end_time: datetime | None = Field(None, description="New end time (ISO format)")
    status: str | None = Field(None, max_length=32, description="Booking status")

    @root_validator
    def validate_times(cls, values):
        """
        Validate that end_time is after start_time if both are provided.
        
        Args:
            values: Dictionary of field values
            
        Returns:
            dict: Validated values
            
        Raises:
            ValueError: If end_time <= start_time
        """
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end and end <= start:
            raise ValueError("end_time must be after start_time")
        return values
    
    @validator('status')
    def validate_status(cls, v):
        """
        Validate that status is one of the allowed values.
        
        Args:
            v: Status value to validate
            
        Returns:
            str: Validated status value
            
        Raises:
            ValueError: If status is not in the list of valid statuses
        """
        if v is None:
            return v
        valid_statuses = ['booked', 'cancelled', 'completed', 'overridden']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
class CancellationRequest(BaseModel):
    """
    Schema for booking cancellation request.
    
    Attributes:
        reason: Optional reason for cancelling the booking
    """
    reason: str | None = Field(None, max_length=500, description="Reason for cancellation")


class OverrideRequest(BaseModel):
    """
    Schema for booking override request (Admin/Manager only).
    
    Attributes:
        reason: Required reason for overriding the booking
    """
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for overriding this booking")
class BookingOut(BaseModel):
    """
    Schema for booking output/response.
    
    Attributes:
        id: Booking ID
        user_id: ID of the user who made the booking
        room_id: ID of the booked room
        start_time: Booking start time
        end_time: Booking end time
        status: Current booking status
        created_at: Timestamp when booking was created
    """
    id: int
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime | None = None

    class Config:
        """Pydantic configuration."""
        orm_mode = True

class AvailabilityCheck(BaseModel):
    """
    Schema for availability check response.
    
    Attributes:
        room_id: ID of the room checked
        available: Whether the room is available for the time slot
        start_time: Start time of the checked period (ISO format string)
        end_time: End time of the checked period (ISO format string)
        conflicting_bookings: List of booking IDs that conflict with the requested time
    """
    room_id: int
    available: bool
    start_time: str
    end_time: str
    conflicting_bookings: list[int] = []