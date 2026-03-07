"""Message business logic and database queries."""

import uuid
from datetime import datetime
from typing import Any

import structlog
from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.models.message import Message
from src.api.schemas.pagination import PaginationParams
from src.chain import build_kg_rag_chain

logger = structlog.get_logger(__name__)

# Chains are expensive to build — cache by chroma_collection name.
_chain_cache: dict[str, Any] = {}


def _get_chain(chroma_collection: str) -> Any:
    if chroma_collection not in _chain_cache:
        _chain_cache[chroma_collection] = build_kg_rag_chain(
            chroma_collection=chroma_collection
        )
    return _chain_cache[chroma_collection]


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
    """Persist a single message and bump the conversation's updated_at.

    When role is 'human', also invokes the RAG chain using the conversation's
    course collection and appends the AI response as a second message.
    Both messages are committed atomically — neither is saved if the other fails.
    Returns the AI message on human turns, the saved message otherwise.
    """
    if role != "human":
        message = Message(conversation_id=conversation.id, role=role, content=content)
        conversation.updated_at = datetime.utcnow()
        db.add(message)
        db.add(conversation)
        await db.commit()
        await db.refresh(message)
        return message

    # Load the course to get the ChromaDB collection name.
    course_result = await db.execute(select(Course).where(Course.id == conversation.course_id))
    course = course_result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    # Build or retrieve the cached chain, validating the collection exists.
    try:
        chain = _get_chain(course.chroma_collection)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Load conversation history in chronological order for the chain.
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(20)
    )
    lc_history = [
        HumanMessage(content=m.content) if m.role == "human" else AIMessage(content=m.content)
        for m in history_result.scalars().all()
    ]

    logger.info("invoking_chain", collection=course.chroma_collection, conversation_id=str(conversation.id))
    answer: str = await chain.ainvoke(
        {
            "question": content,
            "chat_history": lc_history,
            "system_prompt_mode": conversation.system_prompt_mode,
        }
    )

    # Save both messages and bump the conversation timestamp in one commit.
    human_msg = Message(conversation_id=conversation.id, role="human", content=content)
    ai_msg = Message(conversation_id=conversation.id, role="ai", content=answer)
    conversation.updated_at = datetime.utcnow()

    # TODO: we need better error handling for this function
    db.add(human_msg)
    db.add(ai_msg)
    db.add(conversation)
    await db.commit()
    await db.refresh(ai_msg)
    return ai_msg
