"""Conversation context compression and summary persistence."""

from __future__ import annotations

import re
from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.conversation_context_summary import ConversationContextSummary
from src.api.models.message import Message
from src.api.utils.logging_util import get_service_logger, log_conversation_compression
from src.config import get_settings
from src.models import get_llm
from src.prompts.templates import (
    build_conversation_compression_prompt,
    build_conversation_recompression_prompt,
)

logger = get_service_logger(__name__)


def _format_messages_for_summary(messages: list[Message]) -> str:
    """Format a list of messages as a plain-text dialogue transcript for summarisation."""
    lines: list[str] = []
    for message in messages:
        speaker = "Student" if message.role == "human" else "Tutor"
        lines.append(f"{speaker}: {message.content}")
    return "\n".join(lines)


def _estimate_token_count(text: str) -> int:
    """Return a rough provider-agnostic token estimate for compression thresholds."""

    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def _estimate_history_tokens(
    summary: str | None,
    messages: list[Message],
    pending_user_message: str,
) -> int:
    """Estimate the combined token count of the current summary, recent messages, and the pending question."""
    parts: list[str] = []
    cleaned_summary = (summary or "").strip()
    if cleaned_summary:
        parts.append(cleaned_summary)
    transcript = _format_messages_for_summary(messages)
    if transcript:
        parts.append(transcript)
    if pending_user_message.strip():
        parts.append(f"Student: {pending_user_message.strip()}")
    return _estimate_token_count("\n".join(parts))


async def maybe_compress_conversation_history(
    conversation: Conversation,
    pending_user_message: str,
    db: AsyncSession,
) -> tuple[str | None, datetime | None, bool]:
    """Compress older context when needed while keeping the raw message history."""
    summary_result = await db.execute(
        select(ConversationContextSummary).where(
            ConversationContextSummary.conversation_id == conversation.id
        )
    )
    summary_row = summary_result.scalars().first()

    current_summary = summary_row.context_summary if summary_row is not None else None
    summary_created_at = summary_row.created_at if summary_row is not None else None

    messages_query = select(Message).where(Message.conversation_id == conversation.id)
    if summary_created_at is not None:
        messages_query = messages_query.where(Message.created_at > summary_created_at)

    messages_result = await db.execute(
        messages_query.order_by(Message.created_at.asc())
    )
    messages = list(messages_result.scalars().all())

    limit = get_settings().conversation_compression_token_limit
    estimated_tokens = _estimate_history_tokens(current_summary, messages, pending_user_message)
    if estimated_tokens <= limit:
        return current_summary, summary_created_at, False

    if not current_summary and not messages:
        return None, summary_created_at, False

    log_conversation_compression(
        logger,
        "triggered",
        conversation_id=str(conversation.id),
        mode="recompress" if current_summary else "compress",
        estimated_tokens=estimated_tokens,
        token_limit=limit,
        raw_message_count=len(messages),
        had_existing_summary=bool(current_summary),
    )

    transcript = _format_messages_for_summary(messages)
    llm = get_llm(temperature=0.0)
    parser = StrOutputParser()

    if current_summary:
        chain = build_conversation_recompression_prompt() | llm | parser
        new_summary = await chain.ainvoke(
            {
                "existing_summary": current_summary,
                "conversation_history": transcript or "(No newer raw messages.)",
            }
        )
    else:
        chain = build_conversation_compression_prompt() | llm | parser
        new_summary = await chain.ainvoke({"conversation_history": transcript})

    cleaned_summary = new_summary.strip()
    compressed_at = datetime.utcnow()
    if summary_row is None:
        summary_row = ConversationContextSummary(
            conversation_id=conversation.id,
            context_summary=cleaned_summary,
            created_at=compressed_at,
        )
    else:
        summary_row.context_summary = cleaned_summary
        summary_row.created_at = compressed_at
    db.add(summary_row)
    log_conversation_compression(
        logger,
        "completed",
        conversation_id=str(conversation.id),
        mode="recompress" if current_summary else "compress",
        summary_created_at=compressed_at.isoformat(),
        summary_length=len(cleaned_summary),
    )
    return cleaned_summary, compressed_at, True
