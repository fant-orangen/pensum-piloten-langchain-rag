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
    chroma_collection: Optional[str] = None
    course_specific_instructions: Optional[str] = None
    index_version: int
    rebuild_status: str
    rebuild_error: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    name: str
    code: str
    chroma_collection: Optional[str] = None
    description: Optional[str] = None
    course_specific_instructions: Optional[str] = None
    model_config = {"extra": "ignore"}


class CourseInstructionsUpdate(BaseModel):
    course_specific_instructions: Optional[str] = None


class CourseInstructionsRead(BaseModel):
    course_id: uuid.UUID
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


class MissingCandidateRead(BaseModel):
    email: str
    first_name: str
    last_name: str


class EnrollmentImportPreviewRead(BaseModel):
    preview_id: uuid.UUID
    course_id: uuid.UUID
    uploaded_filename: Optional[str] = None
    requested_role: str
    total_rows: int
    accepted_email_count: int
    enrollable_emails: list[str]
    missing_candidates: list[MissingCandidateRead]
    already_enrolled_emails: list[str]
    duplicate_emails: list[str]
    invalid_emails: list[str]
    has_warnings: bool


class EnrollmentImportConfirmRead(BaseModel):
    course_id: uuid.UUID
    requested_role: str
    enrolled_emails: list[str]
    created_emails: list[str]
    already_enrolled_emails: list[str]


class CourseStudentRead(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class CourseDocumentRead(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    original_filename: str
    content_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourseMaterialsStatusRead(BaseModel):
    course_id: uuid.UUID
    rebuild_status: str
    rebuild_error: Optional[str] = None
    index_version: int
    active_scope: Optional[str] = None
    pending_additions: int
    pending_removals: int


class ZipImportResultRead(BaseModel):
    staged: list[CourseDocumentRead]
    staged_count: int
    skipped_count: int
    skipped_names: list[str]
