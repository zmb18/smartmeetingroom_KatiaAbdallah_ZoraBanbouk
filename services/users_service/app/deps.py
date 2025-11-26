"""
Database initialization module for the Users service.

This module sets up the database connection, creates the session factory,
and initializes all database tables based on the defined models.
"""

import os
from common.database import Base, get_engine, get_session_local

# Database connection URL from environment variable with fallback default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://smartuser:smartpass@postgres:5432/smartmeeting")

# Create database session factory and engine
SessionLocal, engine = get_session_local(DATABASE_URL)

# Ensure tables exist for this service's models
Base.metadata.create_all(bind=engine)