"""Schemas for message endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class MessageRead(BaseModel):
    """A single message as returned by the API."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str  # "human" | "ai"
    content: str
    created_at: datetime
    conversation_compression_triggered: bool = False

    model_config = {"from_attributes": True}
