"""Per-conversation compressed context summary and related information to be appended to the system prompt.
This table is only responsible for storing per-conversation, personalised context for response optimisation."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class ConversationContextSummary(SQLModel, table=True):
    __tablename__ = "conversation_context_summary"

    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.id",
        primary_key=True,
    )
    context_summary: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
