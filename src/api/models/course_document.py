"""Course source document table definition."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CourseDocument(SQLModel, table=True):
    __tablename__ = "course_document"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    original_filename: str
    storage_path: str
    content_type: Optional[str] = None
    status: str = Field(default="active")  # "active" | "pending_add" | "pending_remove"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
