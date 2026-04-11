"""
Schemas Pydantic para autenticación.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request body para POST /auth/login."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=255)


class TokenResponse(BaseModel):
    """Response para /auth/login y /auth/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Segundos hasta expiración del access token


class RefreshTokenRequest(BaseModel):
    """Request body para POST /auth/refresh."""

    refresh_token: str = Field(..., min_length=1)


class UserMe(BaseModel):
    """Response para GET /auth/me."""

    id: UUID
    username: str
    email: EmailStr
    role: str
    is_active: bool
    last_login: datetime | None
