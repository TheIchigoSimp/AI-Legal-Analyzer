"""Pydantic models for authentication"""

from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

class UserOut(BaseModel):
    """Response body for user data (never expose password)."""
    username: str
    created_at: str

class Token(BaseModel):
    """Response body for login — contains the JWT."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data decoded from inside a JWT token."""
    username: str
