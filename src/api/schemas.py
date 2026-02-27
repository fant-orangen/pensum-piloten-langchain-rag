"""Pydantic models for the API request / response contracts."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(human|ai)$")
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    mode: Literal["rag", "no_rag"] = "rag"


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
