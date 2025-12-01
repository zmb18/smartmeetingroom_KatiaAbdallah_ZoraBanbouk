"""
Configuration module for Users Service.

Manages environment variables and settings for database connection,
JWT authentication, and service configuration.
"""

import os
from typing import Optional

class Settings:
    """
    Application Settings.
    
    Attributes:
        SQLALCHEMY_DATABASE_URL: Database connection URL
        SECRET_KEY: Secret key for JWT token signing
        ALGORITHM: Algorithm used for JWT encoding (HS256)
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes
        SERVICE_NAME: Name of the service
        DEBUG: Debug mode flag
        API_PREFIX: API route prefix
    """
    

    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@db:5432/users_db"
    )
    

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
   
    SERVICE_NAME: str = "Users Service"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
 
    API_PREFIX: str = "/api/v1"
    
    class Config:
        """Pydantic configuration."""
        case_sensitive = True

settings = Settings()