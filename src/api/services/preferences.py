"""Business logic for preferences endpoints."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.user import User
from src.api.schemas.preferences import SystemPromptMode


async def update_system_prompt_mode(
    current_user: User,
    mode: SystemPromptMode,
    db: AsyncSession,
) -> bool:
    """Persist the authenticated user's selected system prompt mode."""
    current_user.system_prompt_mode = int(mode)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return True
