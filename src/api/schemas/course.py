"""Schemas for course endpoints."""

import uuid

from pydantic import BaseModel


class CourseRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    rag_mode: str

    model_config = {"from_attributes": True}
