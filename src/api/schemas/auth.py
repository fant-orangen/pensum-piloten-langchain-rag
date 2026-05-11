"""Schemas for auth and user endpoints."""

import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for creating a student account.

    Passwords must be at least eight characters; duplicate emails are rejected
    by the service layer with HTTP 409.
    """

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    """Credentials exchanged for a bearer token."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT bearer token returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    """Password change payload.

    `old_password` is required for normal password changes, but omitted when a
    seeded/user-imported account is forced to set its first password.
    """

    old_password: str | None = None
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Safe user representation — never includes the hashed password."""

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    global_role: str
    system_prompt_mode: int
    must_change_password: bool

    model_config = {"from_attributes": True}
