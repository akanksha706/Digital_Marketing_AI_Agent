"""Pydantic schemas for authentication and user management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.db.models import UserRole


class LoginRequest(BaseModel):
    """Credentials required for user sign-in."""
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    """Payload to request password reset instructions."""
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Payload to update own account password."""
    old_password: str
    new_password: str


class UserCreate(BaseModel):
    """Payload for Admin to register a new team member."""
    email: EmailStr
    password: str
    role: UserRole = UserRole.MEMBER
    brand_id: Optional[int] = 1


class UserResponse(BaseModel):
    """Public representation of a team member."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
    is_active: bool
    brand_id: Optional[int]
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT Bearer token and authenticated user payload."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
