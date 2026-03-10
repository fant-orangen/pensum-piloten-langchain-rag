"""Schemas for auth and user endpoints."""

import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Safe user representation — never includes the hashed password."""

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    global_role: str
    system_prompt_mode: int

    model_config = {"from_attributes": True}
