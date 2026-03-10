"""Schemas for message endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class MessageRead(BaseModel):
    """A single message as returned by the API."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str  # "human" | "ai"
    content: str
    # Source documents referenced by the RAG system. None on human messages.
    sources: Optional[Any]
    created_at: datetime
    conversation_compression_triggered: bool = False

    model_config = {"from_attributes": True}


class MessageSourceRead(BaseModel):
    """Resolved source chunk for a persisted message."""

    chunk_id: str
    document: str
    page: str
    content: str
