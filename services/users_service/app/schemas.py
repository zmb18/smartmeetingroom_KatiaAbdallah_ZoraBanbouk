from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from common import security

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    full_name: Optional[str] = Field(None, max_length=120, description="User's full name")
    role: Optional[str] = Field("regular", description="User role")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = [security.ROLE_ADMIN, security.ROLE_REGULAR, security.ROLE_MANAGER, 
                      security.ROLE_MODERATOR, security.ROLE_AUDITOR, security.ROLE_SERVICE]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    full_name: Optional[str] = Field(None, max_length=120, description="User's full name")
    role: Optional[str] = Field(None, description="User role")
    password: Optional[str] = Field(None, min_length=8, description="New password (minimum 8 characters)")
    
    @validator('role')
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = [security.ROLE_ADMIN, security.ROLE_REGULAR, security.ROLE_MANAGER, 
                      security.ROLE_MODERATOR, security.ROLE_AUDITOR, security.ROLE_SERVICE]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
