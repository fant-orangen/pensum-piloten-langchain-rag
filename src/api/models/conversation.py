"""Conversation table definition."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # The student (or teacher) who owns this conversation.
    user_id: uuid.UUID = Field(foreign_key="app_user.id")
    # The course this conversation is scoped to. Determines which ChromaDB
    # collection, documents, and KG are used during retrieval.
    course_id: uuid.UUID = Field(foreign_key="course.id")
    # Optional short title — auto-generated from the first message or set by
    # the user. Null until the first message is sent.
    title: Optional[str] = None
    # System prompt mode fixed at conversation creation time.
    system_prompt_mode: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Bumped on every new message so conversations can be sorted by recency.
    updated_at: datetime = Field(default_factory=datetime.utcnow)
