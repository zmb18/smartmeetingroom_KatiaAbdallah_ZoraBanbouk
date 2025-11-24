import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from common import security


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    full_name: Optional[str] = Field(None, max_length=120, description="User's full name")
    role: Optional[str] = Field("regular", description="User role")

    @validator("username")
    def validate_username(cls, v: str) -> str:
        """Allow only letters, digits and underscores in usernames."""
        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError("Username must contain only letters, digits, and underscores")
        return v

    @validator("role")
    def validate_role(cls, v: str) -> str:
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
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    full_name: Optional[str] = Field(None, max_length=120, description="User's full name")
    role: Optional[str] = Field(None, description="User role")
    password: Optional[str] = Field(
        None, min_length=8, description="New password (minimum 8 characters)"
    )

    @validator("role")
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
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
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordReset(BaseModel):
    new_password: str = Field(
        ..., min_length=8, description="New password (minimum 8 characters)"
    )


class RoleUpdate(BaseModel):
    role: str = Field(..., description="New role for the user")

    @validator("role")
    def validate_role(cls, v: str) -> str:
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
