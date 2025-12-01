"""
Database models for the Bookings service.

This module defines the SQLAlchemy ORM models for managing meeting room bookings,
including booking status tracking, audit trails, and performance indexes.
"""

from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from common.database import Base

class Booking(Base):
    """
    Booking model representing a meeting room reservation.
    
    Attributes:
        id: Primary key for the booking
        user_id: ID of the user who made the booking
        room_id: ID of the room being booked
        start_time: Start time of the booking
        end_time: End time of the booking
        status: Current status of the booking (booked, cancelled, overridden, completed)
        created_at: Timestamp when the booking was created
        modified_at: Timestamp when the booking was last modified
        modified_by: ID of the user who last modified the booking
        attendee_count: Optional number of attendees for the booking
        cancellation_reason: Reason provided when booking is cancelled
        override_reason: Reason provided when booking is overridden by admin/manager
        
    Indexes:
        idx_room_time: Composite index on (room_id, start_time, end_time) for availability checks
        idx_user_bookings: Composite index on (user_id, start_time) for user booking queries
        idx_status: Index on status for filtering by booking status
        idx_created_at: Index on created_at for chronological queries
    """
    __tablename__ = "bookings"
    
   
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    room_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(32), default="booked")  
    
    
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_by = Column(Integer, nullable=True)  
    
    
    attendee_count = Column(Integer, nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    override_reason = Column(String(500), nullable=True)
    
   
    __table_args__ = (
        Index('idx_room_time', 'room_id', 'start_time', 'end_time'),
        Index('idx_user_bookings', 'user_id', 'start_time'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )