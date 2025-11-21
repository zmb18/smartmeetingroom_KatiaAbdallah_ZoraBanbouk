"""
Configuration module for Users Service
Manages environment variables and settings
"""
import os
from typing import Optional

class Settings:
    """Application Settings"""
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@db:5432/users_db"
    )
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Service Configuration
    SERVICE_NAME: str = "Users Service"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Configuration
    API_PREFIX: str = "/api/v1"
    
    class Config:
        case_sensitive = True

settings = Settings()