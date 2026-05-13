"""Staged course enrollment import preview table definition."""

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from src.api.models.time import utc_timestamp_field


class EnrollmentImportPreview(SQLModel, table=True):
    """Staged bulk enrollment import parsed from a CSV upload, pending teacher review.

    Holds candidate emails and a name map as JSON so the teacher can inspect and
    confirm before the records are committed as real CourseEnrollment rows.
    """

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
    # Maps normalised email → {"first_name": str, "last_name": str} as parsed from the CSV.
    candidates_name_map: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = utc_timestamp_field()
