from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from common.database import Base

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    room_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(32), default="booked")  # booked, cancelled, overridden
    created_at = Column(DateTime, default=datetime.utcnow)
