"""Message business logic and database queries."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.models.message import Message
from src.api.services.conversation_context_summaries import (
    maybe_compress_conversation_history,
)
from src.api.schemas.pagination import PaginationParams
from src.api.utils import bind_log_context, get_service_logger, log_chain_invocation
from src.chain import build_kg_rag_chain
from src.kg.retriever import get_kg_retriever

logger = get_service_logger(__name__)

# Chains are expensive to build — cache by active course scope.
_chain_cache: dict[str, Any] = {}


def _get_chain(scope: str) -> Any:
    if scope not in _chain_cache:
        _chain_cache[scope] = build_kg_rag_chain(
            chroma_collection=scope,
            graph_scope=scope,
        )
    return _chain_cache[scope]


def _serialize_source_documents(docs: list[Any]) -> list[dict[str, Any]]:
    """Convert retrieved documents into source references for persistence."""
    serialized: list[dict[str, Any]] = []
    for doc in docs:
        metadata = doc.metadata if hasattr(doc, "metadata") and isinstance(doc.metadata, dict) else {}
        chunk_id = metadata.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            continue
        serialized.append(
            {
                "chunk_id": chunk_id.strip(),
                "source_file": str(metadata.get("source_file") or "").strip(),
                "page": str(metadata.get("page") or "").strip(),
            }
        )
    return serialized


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
) -> tuple[Message, bool]:
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
        return message, False

    # Load the course to get the ChromaDB collection name.
    course_result = await db.execute(select(Course).where(Course.id == conversation.course_id))
    course = course_result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    if not course.chroma_collection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This course does not currently have ingested materials.",
        )

    # Build or retrieve the cached chain, validating the collection exists.
    try:
        chain = _get_chain(course.chroma_collection)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        
    retriever = get_kg_retriever(
        collection_name=course.chroma_collection,
        graph_scope=course.chroma_collection,
    )

    (
        conversation_summary,
        summary_created_at,
        compression_triggered,
    ) = await maybe_compress_conversation_history(
        conversation,
        content,
        db,
    )

    # Load conversation history in chronological order for the chain.
    history_query = select(Message).where(Message.conversation_id == conversation.id)
    if summary_created_at is not None:
        history_query = history_query.where(Message.created_at > summary_created_at) # Only include messages after the summary was created
    history_result = await db.execute(history_query.order_by(Message.created_at.asc()))
    lc_history = [
        HumanMessage(content=m.content) if m.role == "human" else AIMessage(content=m.content)
        for m in history_result.scalars().all()
    ]

    log_chain_invocation(
        bind_log_context(
            logger,
            collection=course.chroma_collection,
            conversation_id=conversation.id,
        )
    )
    # Get serialised sources for the AI message
    source_docs = await retriever.ainvoke(content)
    serialized_sources = _serialize_source_documents(source_docs)
    answer: str = await chain.ainvoke(
        {
            "question": content,
            "chat_history": lc_history,
            "system_prompt_mode": conversation.system_prompt_mode,
            "course_specific_instructions": course.course_specific_instructions,
            "conversation_summary": conversation_summary,
        }
    )

    # Save both messages and bump the conversation timestamp in one commit.
    human_msg = Message(conversation_id=conversation.id, role="human", content=content)
    ai_msg = Message(
        conversation_id=conversation.id,
        role="ai",
        content=answer,
        sources=serialized_sources,
    )
    conversation.updated_at = datetime.utcnow()

    # TODO: we need better error handling for this function
    db.add(human_msg)
    db.add(ai_msg)
    db.add(conversation)
    await db.commit()
    await db.refresh(ai_msg)
    return ai_msg, compression_triggered
