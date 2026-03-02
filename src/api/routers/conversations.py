"""Conversation endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.conversation import ConversationRead
from src.api.schemas.pagination import Page, PaginationParams
from src.api.services.conversations import get_user_conversations

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=Page[ConversationRead])
async def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[ConversationRead]:
    """Return paginated conversations for the authenticated user.

    Ordered by most recent activity (updated_at descending).
    """
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_user_conversations(current_user.id, params, db)
    return Page.create(items=[ConversationRead.model_validate(c) for c in items], total=total, params=params)
