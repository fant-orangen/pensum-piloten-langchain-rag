"""Message business logic and database queries."""

import uuid
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.models.message import Message
from src.api.models.time import utc_now
from src.api.services.conversation_context_summaries import (
    maybe_compress_conversation_history,
)
from src.api.services.source_metadata import extract_source_page
from src.api.schemas.pagination import PaginationParams
from src.api.utils.exception_util import bad_request_error, not_found_error, stage_error
from src.api.utils import bind_log_context, get_service_logger, log_chain_invocation
from src.chain import build_kg_rag_chain, build_naive_rag_chain

logger = get_service_logger(__name__)

# Chains are expensive to build — cache by active course scope.
_chain_cache: dict[tuple[str, str], Any] = {}


def _get_chain(scope: str, rag_mode: str) -> Any:
    """Return a cached course RAG chain for the given mode and collection scope."""
    cache_key = (rag_mode, scope)
    if cache_key not in _chain_cache:
        if rag_mode == "kg_rag":
            _chain_cache[cache_key] = build_kg_rag_chain(
                chroma_collection=scope,
                graph_scope=scope,
            )
        elif rag_mode == "naive_rag":
            _chain_cache[cache_key] = build_naive_rag_chain(chroma_collection=scope)
        else:
            raise ValueError(f"Unsupported course RAG mode: {rag_mode}")
    return _chain_cache[cache_key]


def _serialize_source_documents(docs: list[Any]) -> list[dict[str, Any]]:
    """Convert retrieved documents into source references for persistence."""
    serialized: list[dict[str, Any]] = []
    for doc in docs:
        metadata = (
            doc.metadata if hasattr(doc, "metadata") and isinstance(doc.metadata, dict) else {}
        )
        chunk_id = metadata.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            continue
        serialized.append(
            {
                "chunk_id": chunk_id.strip(),
                "source_file": str(metadata.get("source_file") or "").strip(),
                "page": extract_source_page(metadata),
            }
        )
    return serialized


def _unpack_chain_result(result: Any) -> tuple[str, list[Any]]:
    """Extract the answer and exact retrieved docs from the KG-RAG chain result."""
    if not isinstance(result, dict):
        raise TypeError("KG-RAG chain returned an invalid result.")

    answer = result.get("answer")
    if not isinstance(answer, str):
        raise TypeError("KG-RAG chain result is missing a string answer.")

    source_documents = result.get("source_documents", [])
    if not isinstance(source_documents, list):
        raise TypeError("KG-RAG chain result has invalid source documents.")

    return answer, source_documents


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
        base.order_by(Message.created_at.desc()).offset(params.offset).limit(params.page_size)
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
        conversation.updated_at = utc_now()
        db.add(message)
        db.add(conversation)
        try:
            await db.commit()
            await db.refresh(message)
        except SQLAlchemyError as exc:
            await db.rollback()
            logger.exception("message_persistence_failed", conversation_id=conversation.id)
            raise stage_error(
                "message_persistence_failed",
                "Failed to save the message to the database.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from exc
        return message, False

    # Load the course to get the ChromaDB collection name.
    course_result = await db.execute(select(Course).where(Course.id == conversation.course_id))
    course = course_result.scalars().first()
    if course is None:
        raise not_found_error("Course not found.")

    if not course.chroma_collection:
        raise bad_request_error("This course does not currently have ingested materials.")

    # Build or retrieve the cached chain, validating the collection exists.
    try:
        chain = _get_chain(course.chroma_collection, course.rag_mode)
    except ValueError as exc:
        raise stage_error(
            "message_chain_configuration_invalid",
            str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except Exception as exc:
        logger.exception(
            "message_chain_initialization_failed",
            conversation_id=conversation.id,
            collection=course.chroma_collection,
            rag_mode=course.rag_mode,
        )
        raise stage_error(
            "message_chain_initialization_failed",
            "Failed to initialize the tutor agent for this course.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    try:
        (
            conversation_summary,
            summary_created_at,
            compression_triggered,
        ) = await maybe_compress_conversation_history(
            conversation,
            content,
            db,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("message_history_compression_failed", conversation_id=conversation.id)
        raise stage_error(
            "message_history_compression_failed",
            "Failed to prepare the conversation history for this message.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    # Load conversation history in chronological order for the chain.
    history_query = select(Message).where(Message.conversation_id == conversation.id)
    if summary_created_at is not None:
        history_query = history_query.where(
            Message.created_at > summary_created_at
        )  # Only include messages after the summary was created
    try:
        history_result = await db.execute(history_query.order_by(Message.created_at.asc()))
    except SQLAlchemyError as exc:
        logger.exception("message_history_load_failed", conversation_id=conversation.id)
        raise stage_error(
            "message_history_load_failed",
            "Failed to load the conversation history for this message.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
    lc_history = [
        HumanMessage(content=m.content) if m.role == "human" else AIMessage(content=m.content)
        for m in history_result.scalars().all()
    ]

    log_chain_invocation(
        bind_log_context(
            logger,
            collection=course.chroma_collection,
            conversation_id=conversation.id,
            rag_mode=course.rag_mode,
        )
    )
    try:
        chain_result = await chain.ainvoke(
            {
                "question": content,
                "chat_history": lc_history,
                "system_prompt_mode": conversation.system_prompt_mode,
                "course_specific_instructions": course.course_specific_instructions,
                "conversation_summary": conversation_summary,
            }
        )
        answer, source_docs = _unpack_chain_result(chain_result)
        serialized_sources = _serialize_source_documents(source_docs)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "message_agent_response_failed",
            conversation_id=conversation.id,
            collection=course.chroma_collection,
        )
        raise stage_error(
            "message_agent_response_failed",
            "Failed to obtain a response from the tutor agent.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc

    # Save both messages and bump the conversation timestamp in one commit.
    human_msg = Message(conversation_id=conversation.id, role="human", content=content)
    ai_msg = Message(
        conversation_id=conversation.id,
        role="ai",
        content=answer,
        sources=serialized_sources,
    )
    conversation.updated_at = utc_now()

    try:
        db.add(human_msg)
        db.add(ai_msg)
        db.add(conversation)
        await db.commit()
        await db.refresh(ai_msg)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("message_persistence_failed", conversation_id=conversation.id)
        raise stage_error(
            "message_persistence_failed",
            "Failed to save the generated conversation messages.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
    return ai_msg, compression_triggered
