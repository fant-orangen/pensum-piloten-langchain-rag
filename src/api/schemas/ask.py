"""Pydantic models for the /ask request / response contracts."""

from typing import Literal

from pydantic import BaseModel, Field

from src.api.schemas.preferences import SystemPromptMode


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(human|ai)$")
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    mode: Literal["rag", "reranked_rag", "no_rag"] = "rag"
    system_prompt_mode: SystemPromptMode = SystemPromptMode.SOCRATIC


class AskResponse(BaseModel):
    answer: str
