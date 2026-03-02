"""Message business logic and database queries."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
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


async def create_message(
    conversation: Conversation,
    content: str,
    role: str,
    db: AsyncSession,
) -> Message:
    """Persist a single message and bump the conversation's updated_at."""
    message = Message(conversation_id=conversation.id, role=role, content=content)
    conversation.updated_at = datetime.utcnow()

    db.add(message)
    db.add(conversation)
    await db.commit()
    await db.refresh(message)
    return message
