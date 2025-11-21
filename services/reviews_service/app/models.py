from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from common.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    room_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(1000), nullable=True)
    flagged = Column(Boolean, default=False)
    hidden = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
