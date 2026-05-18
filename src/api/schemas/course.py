"""Schemas for course endpoints."""

import uuid
from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import BaseModel

CourseRagMode = Literal["kg_rag", "naive_rag"]


class CourseRead(BaseModel):
    """Full course representation used on teacher/admin pages.

    `rebuild_status` is one of idle/queued/building/failed; `index_version`
    tracks the active material index version.
    """

    id: uuid.UUID
    name: str
    code: str
    rag_mode: CourseRagMode
    chroma_collection: Optional[str] = None
    course_specific_instructions: Optional[str] = None
    index_version: int
    rebuild_status: str
    rebuild_error: Optional[str] = None
    created_by_id: uuid.UUID

    model_config = {"from_attributes": True}


class CourseSummaryRead(BaseModel):
    """Minimal course representation for chat and navigation."""

    id: uuid.UUID
    name: str
    code: str

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    """Payload for creating a course.

    `documents_dir` is accepted for API compatibility, but the service derives
    the actual storage directory from the course code.
    """

    name: str
    code: str
    chroma_collection: Optional[str] = None
    documents_dir: str
    description: Optional[str] = None
    rag_mode: CourseRagMode = "naive_rag"
    course_specific_instructions: Optional[str] = None


class CourseInstructionsUpdate(BaseModel):
    """Update course-specific prompt instructions."""

    course_specific_instructions: Optional[str] = None


class CourseInstructionsRead(BaseModel):
    """Read model for course-specific prompt instructions."""

    course_id: uuid.UUID
    course_specific_instructions: Optional[str] = None


class EnrollmentCreate(BaseModel):
    """Request to enroll an existing user by email."""

    # Email of the user to enroll; looked up server-side.
    user_email: str
    role: str = "student"  # "student" | "teacher"


class EnrollmentRead(BaseModel):
    """Enrollment relation returned after add/remove operations."""

    user_id: uuid.UUID
    course_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}


class MissingCandidateRead(BaseModel):
    """CSV import row where no existing user matched the email."""

    email: str
    first_name: str
    last_name: str


class EnrollmentImportPreviewRead(BaseModel):
    """Preview of a CSV enrollment import before it mutates enrollments."""

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
    """Result of confirming a previously previewed enrollment import."""

    course_id: uuid.UUID
    requested_role: str
    enrolled_emails: list[str]
    created_emails: list[str]
    already_enrolled_emails: list[str]


class CourseStudentRead(BaseModel):
    """Compact user representation for course student/teacher lists."""

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class CourseDocumentRead(BaseModel):
    """Source material record and staging state for a course."""

    id: uuid.UUID
    course_id: uuid.UUID
    original_filename: str
    content_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourseMaterialsStatusRead(BaseModel):
    """Current document rebuild state for a course."""

    course_id: uuid.UUID
    rebuild_status: str
    rebuild_error: Optional[str] = None
    index_version: int
    active_scope: Optional[str] = None
    pending_additions: int
    pending_removals: int


class ZipImportResultRead(BaseModel):
    """Result of extracting and staging supported files from a zip upload."""

    staged: list[CourseDocumentRead]
    staged_count: int
    skipped_count: int
    skipped_names: list[str]
