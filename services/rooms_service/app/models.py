from sqlalchemy import Column, Integer, String, Boolean, JSON
from common.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    capacity = Column(Integer, nullable=False)
    equipment = Column(JSON, default=list)  # store as JSON array for portability
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
