"""Preferences endpoints — user-configurable tutoring style (system prompt mode)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_app_user
from src.api.models.user import User
from src.api.schemas.preferences import (
    SystemPromptPreferenceUpdateRequest,
    SystemPromptPreferenceUpdateResponse,
)
from src.api.services.preferences import update_system_prompt_mode

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.patch("/system-prompt", response_model=SystemPromptPreferenceUpdateResponse)
async def set_system_prompt_mode(
    request: SystemPromptPreferenceUpdateRequest,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> SystemPromptPreferenceUpdateResponse:
    """Update the active system prompt mode for the authenticated user."""
    success = await update_system_prompt_mode(current_user, request.mode, db)
    message = (
        "System prompt mode updated successfully."
        if success
        else "Failed to update system prompt mode."
    )
    return SystemPromptPreferenceUpdateResponse(
        success=success,
        message=message,
        mode=request.mode,
    )
