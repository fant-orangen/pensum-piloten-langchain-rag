"""Message table definition."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.api.models.time import utc_timestamp_field


class Message(SQLModel, table=True):
    """A single human or AI turn within a conversation.

    AI messages may carry a JSONB ``sources`` list of RAG chunks used to produce
    the response, enabling source attribution without a separate join table.
    """

    __tablename__ = "message"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("conversation.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role: str  # "human" | "ai"
    content: str
    # Source documents used by the RAG system to produce this message.
    # Only populated on AI messages. Stored as JSONB so individual fields
    # (filename, chunk_id) are indexable without a separate join table.
    # Example: [{"filename": "memory.pdf", "chunk_id": "abc123"}]
    sources: Optional[Any] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime = utc_timestamp_field()
