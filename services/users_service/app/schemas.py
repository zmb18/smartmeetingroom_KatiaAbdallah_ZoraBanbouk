"""
Pydantic schemas for the Users service.

This module defines the request and response schemas for user operations,
including validation rules for usernames, passwords, emails, and roles.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from common import security


class UserCreate(BaseModel):
    """
    Schema for creating a new user account.
    
    Attributes:
        username: Username (3-50 characters, alphanumeric and underscores only)
        password: Password (minimum 8 characters)
        email: Valid email address
        full_name: Optional full name of the user
        role: User role (defaults to 'regular')
        
    Validation:
        - Username must contain only letters, digits, and underscores
        - Role must be one of the predefined valid roles
    """
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    full_name: Optional[str] = Field(None, max_length=120, description="User's full name")
    role: Optional[str] = Field("regular", description="User role")

    @validator("username")
    def validate_username(cls, v: str) -> str:
        """
        Allow only letters, digits and underscores in usernames.
        
        Args:
            v: Username value to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username contains invalid characters
        """
        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError("Username must contain only letters, digits, and underscores")
        return v

    @validator("role")
    def validate_role(cls, v: str) -> str:
        """
        Validate that role is one of the allowed values.
        
        Args:
            v: Role value to validate
            
        Returns:
            str: Validated role
            
        Raises:
            ValueError: If role is not in the list of valid roles
        """
        valid_roles = [
            security.ROLE_ADMIN,
            security.ROLE_REGULAR,
            security.ROLE_MANAGER,
            security.ROLE_MODERATOR,
            security.ROLE_AUDITOR,
            security.ROLE_SERVICE,
        ]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user.
    
    Attributes:
        email: Optional new email address
        full_name: Optional new full name
        role: Optional new role
        password: Optional new password (minimum 8 characters)
        
    Validation:
        - Role must be one of the predefined valid roles if provided
    """
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    full_name: Optional[str] = Field(None, max_length=120, description="User's full name")
    role: Optional[str] = Field(None, description="User role")
    password: Optional[str] = Field(
        None, min_length=8, description="New password (minimum 8 characters)"
    )

    @validator("role")
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that role is one of the allowed values if provided.
        
        Args:
            v: Role value to validate
            
        Returns:
            str | None: Validated role or None
            
        Raises:
            ValueError: If role is not in the list of valid roles
        """
        if v is None:
            return v
        valid_roles = [
            security.ROLE_ADMIN,
            security.ROLE_REGULAR,
            security.ROLE_MANAGER,
            security.ROLE_MODERATOR,
            security.ROLE_AUDITOR,
            security.ROLE_SERVICE,
        ]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v


class UserOut(BaseModel):
    """
    Schema for user output/response.
    
    Attributes:
        id: User ID
        username: Username
        email: Email address
        full_name: Full name of the user
        role: User role
        is_active: Whether the account is active
        created_at: Timestamp when the user was created
    """
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        orm_mode = True


class Token(BaseModel):
    """
    Schema for JWT token response.
    
    Attributes:
        access_token: JWT access token string
        token_type: Token type (always 'bearer')
    """
    access_token: str
    token_type: str = "bearer"


class PasswordReset(BaseModel):
    """
    Schema for password reset request.
    
    Attributes:
        new_password: New password (minimum 8 characters)
    """
    new_password: str = Field(
        ..., min_length=8, description="New password (minimum 8 characters)"
    )


class RoleUpdate(BaseModel):
    """
    Schema for updating a user's role.
    
    Attributes:
        role: New role for the user
        
    Validation:
        - Role must be one of the predefined valid roles
    """
    role: str = Field(..., description="New role for the user")

    @validator("role")
    def validate_role(cls, v: str) -> str:
        """
        Validate that role is one of the allowed values.
        
        Args:
            v: Role value to validate
            
        Returns:
            str: Validated role
            
        Raises:
            ValueError: If role is not in the list of valid roles
        """
        valid_roles = [
            security.ROLE_ADMIN,
            security.ROLE_REGULAR,
            security.ROLE_MANAGER,
            security.ROLE_MODERATOR,
            security.ROLE_AUDITOR,
            security.ROLE_SERVICE,
        ]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v