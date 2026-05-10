"""Message business logic and course-coded experiment routing."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.models.message import Message
from src.api.services.conversation_context_summaries import (
    maybe_compress_conversation_history,
)
from src.api.schemas.pagination import PaginationParams
from src.api.utils.exception_util import bad_request_error, not_found_error, stage_error
from src.api.utils import bind_log_context, get_service_logger, log_chain_invocation
from src.chain import (
    build_kg_rag_chain,
    build_no_rag_chain,
    build_rag_chain,
    build_reranked_rag_chain,
)

logger = get_service_logger(__name__)

_RAG_COURSE_CODE = "os_g1"
_SYS_COURSE_CODE = "os_g2"
_CONTROL_COURSE_CODE = "os_g3"

# Chains are expensive to build — cache by strategy, scope, and prompt variant.
_chain_cache: dict[tuple[str, str | None, str], Any] = {}


def _experiment_strategy_for_course(course: Course) -> tuple[str, str]:
    """Return (chain_kind, prompt_variant) for the active course."""
    course_code = str(course.code or "").strip().lower()
    if course_code == _RAG_COURSE_CODE:
        return "kg_rag", "default"
    if course_code == _SYS_COURSE_CODE:
        return "no_rag", "default"
    if course_code == _CONTROL_COURSE_CODE:
        return "no_rag", "control"
    if course.rag_mode in {"rag", "reranked_rag", "no_rag"}:
        return course.rag_mode, "default"
    return "kg_rag", "default"


def _get_chain(
    *,
    chain_kind: str,
    scope: str | None,
    prompt_variant: str,
) -> Any:
    """Return a cached chain for the given routing combination."""
    cache_key = (chain_kind, scope, prompt_variant)
    chain = _chain_cache.get(cache_key)
    if chain is not None:
        return chain

    if chain_kind in {"kg_rag", "rag", "reranked_rag"}:
        if not scope:
            raise ValueError("This course does not currently have ingested materials.")
    if chain_kind == "kg_rag":
        chain = build_kg_rag_chain(
            chroma_collection=scope,
            graph_scope=scope,
            prompt_variant=prompt_variant,
        )
    elif chain_kind == "rag":
        chain = build_rag_chain(
            chroma_collection=scope,
            prompt_variant=prompt_variant,
        )
    elif chain_kind == "reranked_rag":
        chain = build_reranked_rag_chain(
            chroma_collection=scope,
            prompt_variant=prompt_variant,
        )
    elif chain_kind == "no_rag":
        chain = build_no_rag_chain(prompt_variant=prompt_variant)
    else:
        raise ValueError(f"Unsupported chain kind: {chain_kind}")

    _chain_cache[cache_key] = chain
    return chain


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

    chain_kind, prompt_variant = _experiment_strategy_for_course(course)

    if chain_kind == "kg_rag" and not course.chroma_collection:
        raise bad_request_error("This course does not currently have ingested materials.")

    try:
        chain = _get_chain(
            chain_kind=chain_kind,
            scope=course.chroma_collection,
            prompt_variant=prompt_variant,
        )
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
        history_query = history_query.where(Message.created_at > summary_created_at)  # Only include messages after the summary was created
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
            chain_kind=chain_kind,
            prompt_variant=prompt_variant,
        )
    )

    try:
        answer: str = await chain.ainvoke(
            {
                "question": content,
                "chat_history": lc_history,
                "course_specific_instructions": course.course_specific_instructions,
                "conversation_summary": conversation_summary,
            }
        )
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
    )
    conversation.updated_at = datetime.utcnow()

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
