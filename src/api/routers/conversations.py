"""Conversation endpoints — CRUD for conversations and their messages.

All endpoints are scoped to the authenticated user; only the conversation
owner may read, write, rename, or delete a conversation and its messages.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_app_user
from src.api.models.user import User
from src.api.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationTitleUpdate,
)
from src.api.schemas.message import MessageCreate, MessageRead, MessageSourceRead
from src.api.schemas.pagination import Page, PaginationParams
from src.api.services.conversations import (
    create_conversation,
    delete_conversation_for_user,
    get_conversation_for_user,
    get_user_conversations,
    rename_conversation_for_user,
)
from src.api.services.message_sources import get_message_sources_for_user
from src.api.services.messages import create_message, get_conversation_messages

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=Page[ConversationRead])
async def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    course_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> Page[ConversationRead]:
    """Return paginated conversations for the authenticated user.

    Ordered by most recent activity (updated_at descending).
    """
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_user_conversations(current_user.id, params, db, course_id=course_id)
    return Page.create(
        items=[ConversationRead.model_validate(c) for c in items], total=total, params=params
    )


@router.get("/{conversation_id}/messages", response_model=Page[MessageRead])
async def list_messages(
    conversation_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> Page[MessageRead]:
    """Return paginated messages for a conversation, newest first.

    Only the owner of the conversation may access it.
    Reverse each page client-side to display messages in chronological order.
    """
    await get_conversation_for_user(conversation_id, current_user.id, db)
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_conversation_messages(conversation_id, params, db)
    return Page.create(
        items=[MessageRead.model_validate(m) for m in items], total=total, params=params
    )


@router.get(
    "/{conversation_id}/messages/{message_id}/sources",
    response_model=list[MessageSourceRead],
)
async def get_message_sources(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageSourceRead]:
    """Return the RAG source chunks attached to an AI message.

    Only the conversation owner may access message sources.
    """
    sources = await get_message_sources_for_user(
        conversation_id,
        message_id,
        current_user.id,
        db,
    )
    return [MessageSourceRead.model_validate(source) for source in sources]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def new_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    """Start a new conversation in a course the user is enrolled in."""
    conversation = await create_conversation(
        current_user.id,
        request.course_id,
        current_user.system_prompt_mode,
        db,
    )
    return ConversationRead.model_validate(conversation)


@router.post(
    "/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED
)
async def new_message(
    conversation_id: uuid.UUID,
    request: MessageCreate,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    """Add a message to an existing conversation."""
    conversation = await get_conversation_for_user(conversation_id, current_user.id, db)
    message, compression_triggered = await create_message(
        conversation,
        request.content,
        "human",
        db,
    )
    return MessageRead.model_validate(message).model_copy(
        update={"conversation_compression_triggered": compression_triggered}
    )


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: ConversationTitleUpdate,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    """Rename a conversation owned by the authenticated user."""
    conversation = await rename_conversation_for_user(
        conversation_id, current_user.id, body.title, db
    )
    return ConversationRead.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation owned by the authenticated user."""
    await delete_conversation_for_user(conversation_id, current_user.id, db)
