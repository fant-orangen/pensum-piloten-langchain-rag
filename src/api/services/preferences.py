"""Business logic for preferences endpoints."""

from src.api.models.user import User
from src.api.schemas.preferences import SystemPromptMode


async def update_system_prompt_mode(
    current_user: User,
    mode: SystemPromptMode,
) -> bool:
    """Prepare the system prompt mode update.

    TODO: Complete the actual backend system prompt update here.

    The API layer is wired and validated, but the real prompt-switching logic
    should be implemented later when the backend behavior is finalized.
    """
    _ = current_user
    _ = mode
    return True
