"""Schemas for message endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class MessageRead(BaseModel):
    """A single message as returned by the API."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str  # "human" | "ai"
    content: str
    # Source documents referenced by the RAG system. None on human messages.
    sources: Optional[Any]
    created_at: datetime

    model_config = {"from_attributes": True}
