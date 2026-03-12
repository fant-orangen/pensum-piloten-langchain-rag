"""Message source resolution for persisted AI messages.

This module provides a utility function to resolve and return human-meaningful source
document details for a given AI-generated message in a conversation. It is used for
displaying which document chunks from the vectorstore contributed to an AI message.

Main responsibilities:
- Securely check user access to a conversation and message.
- Retrieve the corresponding course to determine the ChromaDB collection.
- Gather all referenced source chunks, map to their content and document info.
- Extract document/page metadata as best-effort for display purposes.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.course import Course
from src.api.models.message import Message
from src.api.services.conversations import get_conversation_for_user
from src.api.utils.exception_util import not_found_error
from src.api.services.source_metadata import extract_source_page
from src.vectorstore import get_chunks_by_ids


def _extract_chunk_id(source: Any) -> str | None:
    """
    Extracts the chunk ID from a source dict, or returns None if not found.
    The chunk ID is expected as a non-empty string under the 'chunk_id' key.
    """
    if not isinstance(source, dict):
        return None
    chunk_id = source.get("chunk_id")
    if not isinstance(chunk_id, str):
        return None
    candidate = chunk_id.strip()
    return candidate or None


def _source_document(source: dict[str, Any], fallback: dict[str, Any]) -> str:
    """
    Extracts the displayable document name or file name from a source dict, using a fallback.
    Checks a prioritized list of keys in source; if nothing is found, looks in fallback metadata.
    Returns a default placeholder if no document info present.
    """
    for key in ("document", "source_file", "filename", "file", "source", "name"):
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    meta_value = fallback.get("source_file")
    if isinstance(meta_value, str) and meta_value.strip():
        return meta_value.strip()
    return "Ukjent dokument"


def _source_page(source: dict[str, Any], fallback: dict[str, Any]) -> str:
    """
    Extracts the page number or other page indicator for a chunk source, as a string.
    Looks in the source dict, then in the fallback.
    Returns an empty string if not present.
    """
    return extract_source_page(source, fallback)


async def get_message_sources_for_user(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict[str, str]]:
    """
    Resolves the source references for an AI-generated message to their associated
    vectorstore chunks, returning relevant document, page, and chunk content info.

    Parameters:
        conversation_id: UUID of the conversation containing the message.
        message_id:      UUID of the message whose sources are to be resolved.
        user_id:         UUID of the user requesting the source info (for access control).
        db:              SQLAlchemy AsyncSession bound to the current transaction.

    Returns:
        A list of dicts, each containing:
            - 'chunk_id': ID of the chunk.
            - 'document': Name or path to the source document.
            - 'page':     Page number or section within the source document.
            - 'content':  Text content of the chunk.

        Returns an empty list if no sources are found or on error.

    Raises:
        HTTPException 404 if the conversation, message, or course is not found,
        or if the user does not have access to the conversation.
    """
    # Ensure the user has access to the given conversation.
    conversation = await get_conversation_for_user(conversation_id, user_id, db)

    # Load the actual message and check it belongs to the conversation.
    message_result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation.id,
        )
    )
    message = message_result.scalars().first()
    if message is None:
        raise not_found_error("Message not found.")

    # Get the raw sources (chunk references) for this message.
    raw_sources = message.sources
    if not isinstance(raw_sources, list):
        return []

    # Get course/chroma collection for fetching relevant chunks.
    course_result = await db.execute(select(Course).where(Course.id == conversation.course_id))
    course = course_result.scalars().first()
    if course is None:
        raise not_found_error("Course not found.")
    if not course.chroma_collection:
        return []

    # Extract all chunk_ids referenced from the message's sources.
    chunk_ids = [
        chunk_id
        for source in raw_sources
        if isinstance(source, dict)
        if (chunk_id := _extract_chunk_id(source)) is not None
    ]
    if not chunk_ids:
        return []

    # Fetch the vectorstore chunks by ID for this course's chroma collection.
    chunks = get_chunks_by_ids(chunk_ids, collection_name=course.chroma_collection)
    chunk_by_id = {
        str(chunk.metadata.get("chunk_id")).strip(): chunk
        for chunk in chunks
        if isinstance(chunk.metadata, dict) and chunk.metadata.get("chunk_id") is not None
    }

    # Map chunk reference -> detailed document/page/content info for UI display.
    resolved_sources: list[dict[str, str]] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        chunk_id = _extract_chunk_id(source)
        if chunk_id is None:
            continue
        chunk = chunk_by_id.get(chunk_id)
        if chunk is None:
            continue
        metadata = chunk.metadata if isinstance(chunk.metadata, dict) else {}
        resolved_sources.append(
            {
                "chunk_id": chunk_id,
                "document": _source_document(source, metadata),
                "page": _source_page(source, metadata),
                "content": chunk.page_content,
            }
        )

    return resolved_sources
