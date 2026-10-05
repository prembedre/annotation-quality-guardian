"""
User schemas.

Provides request and response schemas for authentication and user management.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user (Admin-only registration)."""

    email: EmailStr = Field(..., description="User's email address (must be unique)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Display name")
    password: str = Field(..., min_length=8, description="Plain-text password (hashed before storage)")
    role: UserRole = Field(default=UserRole.ANNOTATOR, description="Assigned role")


class UserResponse(BaseModel):
    """Schema returned for a user record (never includes hashed_password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    """Schema for the login endpoint."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Plain-text password")


class TokenResponse(BaseModel):
    """Schema returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
