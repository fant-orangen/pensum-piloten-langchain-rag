"""Schemas for preferences endpoints."""

from enum import IntEnum

from pydantic import BaseModel


class SystemPromptMode(IntEnum):
    """Supported system prompt variants."""

    SOCRATIC = 1
    DIRECT = 2
    EXAMPLE = 3


class SystemPromptPreferenceUpdateRequest(BaseModel):
    """Request payload for updating the active system prompt mode."""

    mode: SystemPromptMode


class SystemPromptPreferenceUpdateResponse(BaseModel):
    """Response payload describing whether the update succeeded."""

    success: bool
    message: str
    mode: SystemPromptMode
