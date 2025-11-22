from pydantic import BaseModel, Field, validator
from typing import Optional
import bleach

class ReviewCreate(BaseModel):
    # user_id will be extracted from JWT token, not from request
    # room_id comes from URL path parameter
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    
    @validator("comment", pre=True, always=True)
    def sanitize_comment(cls, v):
        if v is None:
            return v
        # Sanitize to prevent XSS and SQL injection
        clean = bleach.clean(v, tags=[], strip=True, strip_comments=True)
        return clean[:1000]  # enforce max length

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

    @validator("comment", pre=True, always=True)
    def sanitize_comment(cls, v):
        if v is None:
            return v
        clean = bleach.clean(v, tags=[], strip=True, strip_comments=True)
        return clean[:1000]  # enforce max length

class ReviewOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    rating: int
    comment: Optional[str]
    flagged: bool
    hidden: bool

    class Config:
        orm_mode = True
