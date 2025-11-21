import os
from common.database import Base, get_engine, get_session_local

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://smartuser:smartpass@postgres:5432/smartmeeting")
SessionLocal, engine = get_session_local(DATABASE_URL)

# Ensure tables exist for this service's models
Base.metadata.create_all(bind=engine)
