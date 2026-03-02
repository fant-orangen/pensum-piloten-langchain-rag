"""Conversation business logic and database queries."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.schemas.pagination import PaginationParams


async def get_user_conversations(
    user_id: uuid.UUID,
    params: PaginationParams,
    db: AsyncSession,
) -> tuple[list[Conversation], int]:
    """Return a page of conversations for a user, ordered by most recent activity.

    Returns a (items, total) tuple so the router can build a Page response.
    """
    base = select(Conversation).where(Conversation.user_id == user_id)

    count_result = await db.exec(select(func.count()).select_from(base.subquery()))
    total: int = count_result.one()

    result = await db.exec(
        base.order_by(Conversation.updated_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    items = list(result.all())

    return items, total
