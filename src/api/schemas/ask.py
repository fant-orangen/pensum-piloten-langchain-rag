"""Pydantic models for the /ask request / response contracts."""

from typing import Literal

from pydantic import BaseModel, Field

from src.api.schemas.preferences import SystemPromptMode


class ChatMessage(BaseModel):
    """Prior chat turn supplied to the legacy /ask endpoint."""

    role: str = Field(..., pattern="^(human|ai)$")
    content: str


class AskRequest(BaseModel):
    """Request body for the legacy stateless ask endpoint.

    Modern chat flows use persisted conversations instead. This endpoint keeps
    a small explicit history and allows selecting RAG vs no-RAG generation.
    """

    question: str = Field(..., min_length=1, max_length=2000)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    mode: Literal["rag", "no_rag"] = "rag"
    system_prompt_mode: SystemPromptMode = SystemPromptMode.SOCRATIC


class AskResponse(BaseModel):
    """Generated answer plus lightweight source identifiers."""

    answer: str
    sources: list[str]
