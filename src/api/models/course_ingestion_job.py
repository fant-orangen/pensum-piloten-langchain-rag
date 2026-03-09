"""Course ingestion job table definition."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CourseIngestionJob(SQLModel, table=True):
    __tablename__ = "course_ingestion_job"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    triggered_by_id: uuid.UUID = Field(foreign_key="app_user.id")
    status: str = Field(default="queued")  # queued | running | failed | completed
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
