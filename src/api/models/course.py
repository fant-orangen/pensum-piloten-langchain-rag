"""Course table definition."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    """A course offered on the platform, backed by a ChromaDB collection for RAG.

    The active vector/KG scope is tracked via ``chroma_collection`` and ``index_version``;
    re-ingestion builds a new partition and swaps it in atomically on success.
    """

    __tablename__ = "course"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    # Short identifier used in URLs and ingestion paths, e.g. "TDT4186".
    code: str = Field(unique=True, index=True)
    description: Optional[str] = None
    # Active vector/KG scope for this course. A new scope is built during
    # re-ingestion and swapped in only after the rebuild succeeds.
    chroma_collection: Optional[str] = None
    # Relative path (from project root) to this course's source documents.
    documents_dir: str
    # Default RAG chain to use for conversations in this course.
    rag_mode: str = Field(default="kg_rag")  # "rag" | "kg_rag" | "no_rag"
    # Optional teacher-authored instructions appended to the fixed tutor prompt.
    course_specific_instructions: Optional[str] = None
    # Monotonic version used to name new course-scoped vector/KG partitions.
    index_version: int = Field(default=0)
    rebuild_status: str = Field(default="idle")
    rebuild_error: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Teacher who created the course.
    created_by_id: uuid.UUID = Field(foreign_key="app_user.id")
