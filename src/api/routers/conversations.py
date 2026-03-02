"""Conversation endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.conversation import Conversation
from src.api.models.user import User
from src.api.schemas.conversation import ConversationRead
from src.api.schemas.message import MessageRead
from src.api.schemas.pagination import Page, PaginationParams
from src.api.services.conversations import get_user_conversations
from src.api.services.messages import get_conversation_messages

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


@router.get("/{conversation_id}/messages", response_model=Page[MessageRead])
async def list_messages(
    conversation_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[MessageRead]:
    """Return paginated messages for a conversation, newest first.

    Only the owner of the conversation may access it.
    Reverse each page client-side to display messages in chronological order.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalars().first()

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # これなら、ユーザは取得しようとした会話が存在していると知っている。それ最適か。ないなら変更する
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_conversation_messages(conversation_id, params, db)
    return Page.create(items=[MessageRead.model_validate(m) for m in items], total=total, params=params)
