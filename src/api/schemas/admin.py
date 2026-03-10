"""Schemas for admin user management endpoints."""

import uuid

from pydantic import BaseModel


class AdminUserRead(BaseModel):
    """Safe user representation for admin user listings."""

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    global_role: str

    model_config = {"from_attributes": True}
