"""Schemas for conversation endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    course_id: uuid.UUID


class ConversationTitleUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ConversationRead(BaseModel):
    """A single conversation as returned by the API.

    Excludes user_id — the caller is always the authenticated user so
    including it in the response adds no information and leaks an internal ID
    to clients that don't need it.
    """

    id: uuid.UUID
    course_id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
