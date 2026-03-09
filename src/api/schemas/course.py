"""Schemas for course endpoints."""

import uuid
from typing import Optional

from pydantic import BaseModel


class CourseRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    rag_mode: str
    course_specific_instructions: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    name: str
    code: str
    chroma_collection: str
    documents_dir: str
    description: Optional[str] = None
    rag_mode: str = "kg_rag"
    course_specific_instructions: Optional[str] = None


class CourseInstructionsUpdate(BaseModel):
    course_specific_instructions: Optional[str] = None


class EnrollmentCreate(BaseModel):
    # Email of the user to enroll; looked up server-side.
    user_email: str
    role: str = "student"  # "student" | "teacher"


class EnrollmentRead(BaseModel):
    user_id: uuid.UUID
    course_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}
