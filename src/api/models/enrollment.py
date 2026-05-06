"""CourseEnrollment join table — many-to-many between User and Course."""

import uuid
from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class CourseEnrollment(SQLModel, table=True):
    """Many-to-many join between User and Course carrying a per-course role.

    The course-level role (student/teacher) is independent of the user's global_role
    and controls permissions within a single course only.
    """

    __tablename__ = "course_enrollment"
    # Prevent a user from being enrolled in the same course more than once.
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollment"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="app_user.id")
    course_id: uuid.UUID = Field(foreign_key="course.id")
    # Role within this specific course — independent of the user's global_role.
    role: str  # "student" | "teacher"
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
