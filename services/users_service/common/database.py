import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to the shared Postgres instance; can be overridden per process for tests (e.g., sqlite:///...)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://smartuser:smartpass@postgres:5432/smartmeeting")

Base = declarative_base()

def _connect_args(url: str):
    return {"check_same_thread": False} if url.startswith("sqlite") else {}

def get_engine(database_url: str | None = None):
    url = database_url or DATABASE_URL
    return create_engine(url, future=True, connect_args=_connect_args(url))

def get_session_local(database_url: str | None = None):
    engine = get_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine), engine

# Default engine/sessionmaker for convenience (used by services)
SessionLocal, engine = get_session_local()
