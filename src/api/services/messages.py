"""Message business logic and database queries."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.message import Message
from src.api.schemas.pagination import PaginationParams


async def get_conversation_messages(
    conversation_id: uuid.UUID,
    params: PaginationParams,
    db: AsyncSession,
) -> tuple[list[Message], int]:
    """Return a page of messages for a conversation, newest first.

    Ordering by created_at descending means page 1 contains the most recent
    messages. The frontend can reverse each page to display them in
    chronological (human → ai → human → ai) order within the viewport.
    """
    base = select(Message).where(Message.conversation_id == conversation_id)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = count_result.scalar_one()

    result = await db.execute(
        base.order_by(Message.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    items = list(result.scalars().all())

    return items, total
