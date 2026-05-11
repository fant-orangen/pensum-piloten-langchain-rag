"""Per-conversation compressed context summary and related information to be appended to the system prompt.
This table is only responsible for storing per-conversation, personalised context for response optimisation."""

import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, SQLModel

from src.api.models.time import utc_timestamp_field


class ConversationContextSummary(SQLModel, table=True):
    """One-to-one rolling summary of a conversation, appended to the system prompt.

    Uses ``conversation_id`` as its primary key to enforce the one-to-one constraint.
    The summary is updated incrementally as the conversation grows to keep token usage bounded.
    """

    __tablename__ = "conversation_context_summary"

    conversation_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("conversation.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )
    context_summary: str = ""
    created_at: datetime = utc_timestamp_field()
