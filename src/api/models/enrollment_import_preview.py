"""Staged course enrollment import preview table definition."""

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class EnrollmentImportPreview(SQLModel, table=True):
    __tablename__ = "enrollment_import_preview"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    created_by_id: uuid.UUID = Field(foreign_key="app_user.id", index=True)
    uploaded_filename: str | None = None
    requested_role: str = Field(default="student")
    candidate_emails: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
