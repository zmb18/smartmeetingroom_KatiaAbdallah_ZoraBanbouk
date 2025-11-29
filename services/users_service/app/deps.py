"""
Database initialization module for the application.

This module sets up the database connection, creates the session factory,
and initializes all database tables based on the defined models.
Supports both Docker (postgres hostname) and local development (localhost).
"""

import os
from common.database import Base, get_session_local

# Determine database host based on environment
# Use 'postgres' for Docker, 'localhost' for local development
DB_HOST = os.getenv("DB_HOST", "localhost")  # Default to localhost for local dev
DB_USER = os.getenv("DB_USER", "smartuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "smartpass")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "smartmeeting")

# Build database URL from environment variables
# This allows the same code to work in Docker and locally
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print(f"Connecting to database at: {DATABASE_URL.replace(DB_PASSWORD, '***')}")

# Create database session factory and engine
SessionLocal, engine = get_session_local(DATABASE_URL)

# Create all tables in the database if they don't exist
Base.metadata.create_all(bind=engine)
