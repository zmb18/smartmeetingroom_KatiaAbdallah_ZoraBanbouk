import os
from common.database import Base, get_session_local

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://smartuser:smartpass@postgres:5432/smartmeeting")
SessionLocal, engine = get_session_local(DATABASE_URL)

Base.metadata.create_all(bind=engine)
