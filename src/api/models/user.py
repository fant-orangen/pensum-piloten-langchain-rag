"""User table definition."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "app_user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    is_active: bool = True
    # Platform-level role. Controls who can create courses and who can promote
    # others. Course-level roles (student / teacher) live on CourseEnrollment.
    global_role: str = Field(default="student")  # "student" | "teacher" | "superadmin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
