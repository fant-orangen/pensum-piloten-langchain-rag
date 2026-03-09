"""Schemas for course endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CourseRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    rag_mode: str

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    name: str
    code: str
    chroma_collection: str
    documents_dir: str
    description: Optional[str] = None
    rag_mode: str = "kg_rag"


class EnrollmentCreate(BaseModel):
    # Email of the user to enroll; looked up server-side.
    user_email: str
    role: str = "student"  # "student" | "teacher"


class EnrollmentRead(BaseModel):
    user_id: uuid.UUID
    course_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}


class EnrollmentUserRead(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str


class EnrollmentWithUserRead(BaseModel):
    user_id: uuid.UUID
    course_id: uuid.UUID
    role: str
    user: EnrollmentUserRead


class CourseMaterialRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    uploaded_by_id: uuid.UUID
    original_filename: str
    mime_type: Optional[str]
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
