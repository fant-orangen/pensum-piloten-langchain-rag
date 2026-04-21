"""Message table definition."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):
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
    sources: Optional[Any] = Field(default=None, sa_column=Column(JSONB, nullable=True)) # Not used anymore
    created_at: datetime = Field(default_factory=datetime.utcnow)
