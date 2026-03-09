"""Course material table definition."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CourseMaterial(SQLModel, table=True):
    __tablename__ = "course_material"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    uploaded_by_id: uuid.UUID = Field(foreign_key="app_user.id")
    original_filename: str
    storage_path: str
    mime_type: Optional[str] = None
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
