"""Course table definition."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    __tablename__ = "course"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    # Short identifier used in URLs and ingestion paths, e.g. "TDT4186".
    code: str = Field(unique=True, index=True)
    description: Optional[str] = None
    # Name of the ChromaDB collection that holds this course's embeddings.
    # Each course gets an isolated collection so retrieval is fully scoped.
    chroma_collection: str = Field(unique=True)
    # Relative path (from project root) to this course's source documents.
    documents_dir: str
    # Default RAG chain to use for conversations in this course.
    rag_mode: str = Field(default="kg_rag")  # "rag" | "kg_rag" | "no_rag"
    # Optional teacher-authored instructions appended to the fixed tutor prompt.
    course_specific_instructions: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Teacher who created the course.
    created_by_id: uuid.UUID = Field(foreign_key="app_user.id")
