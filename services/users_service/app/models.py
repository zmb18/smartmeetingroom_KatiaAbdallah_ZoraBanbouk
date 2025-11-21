# SQLAlchemy models for the Users service
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime
from common.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    full_name = Column(String(120))
    role = Column(String(32), default="regular")  # admin, regular, manager, moderator, auditor, service
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # booking_history could be a JSON or handled by Bookings service - keep reference minimal
    metadata = Column(JSON, nullable=True)
