# SQLAlchemy models for the Users service
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String

from common.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    full_name = Column(String(120))
    role = Column(
        String(32), default="regular"
    )  # admin, regular, manager, moderator, auditor, service
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # booking_history could be a JSON or handled by Bookings service - keep reference minimal
    metadata = Column(JSON, nullable=True)


class AuditLog(Base):
    """Audit log table to track who did what and when."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(50), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
