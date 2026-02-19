"""Helpers for deterministic document identity across ingest and retrieval.

`chunk_id` is the canonical identity for a chunk. We prefer:
1) metadata["chunk_id"] when present,
2) source + page + chunk_index,
3) source + page + content hash fallback.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from langchain_core.documents import Document


def short_content_hash(text: str, length: int = 8) -> str:
    """Return a short deterministic hash for chunk text."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def document_source(metadata: Mapping[str, Any]) -> str:
    """Pick a stable source identifier from metadata."""
    source = metadata.get("source_path") or metadata.get("source_file") or "unknown"
    return str(source)


def document_page(metadata: Mapping[str, Any]) -> str | int | None:
    """Return the page identifier when available."""
    return metadata.get("page")


def document_chunk_index(metadata: Mapping[str, Any]) -> int | None:
    """Return chunk_index as int when present and parseable."""
    raw = metadata.get("chunk_index")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def build_chunk_id(
    metadata: Mapping[str, Any],
    page_content: str,
    *,
    chunk_index: int | None = None,
) -> str:
    """Build a deterministic chunk id from metadata + content fallback."""
    source = document_source(metadata)
    page = document_page(metadata)
    index = document_chunk_index(metadata) if chunk_index is None else chunk_index

    if page is not None and index is not None:
        return f"{source}:p{page}:c{index}"
    if page is not None:
        return f"{source}:p{page}:h{short_content_hash(page_content)}"
    if index is not None:
        return f"{source}:c{index}"
    return f"{source}:h{short_content_hash(page_content)}"


def ensure_chunk_identity(doc: Document, *, fallback_chunk_index: int | None = None) -> str:
    """Ensure `chunk_index` + `chunk_id` exist; return `chunk_id`."""
    metadata = doc.metadata
    if fallback_chunk_index is not None and document_chunk_index(metadata) is None:
        metadata["chunk_index"] = fallback_chunk_index

    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)

    generated = build_chunk_id(
        metadata=metadata,
        page_content=doc.page_content,
        chunk_index=document_chunk_index(metadata),
    )
    metadata["chunk_id"] = generated
    return generated


def document_dedupe_key(doc: Document) -> str:
    """Stable key used to collapse duplicate chunks deterministically."""
    metadata = doc.metadata
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return f"id:{chunk_id}"

    source = document_source(metadata)
    page = document_page(metadata)
    chunk_index = document_chunk_index(metadata)
    if chunk_index is not None:
        return f"spc:{source}|{page}|{chunk_index}"

    return f"sph:{source}|{page}|{short_content_hash(doc.page_content)}"


def document_debug_fields(doc: Document) -> dict[str, str]:
    """Compact debug fields to diagnose duplicate retrieval rows."""
    metadata = doc.metadata
    raw_chunk_index = metadata.get("chunk_index")
    return {
        "chunk_id": str(metadata.get("chunk_id") or "-"),
        "source": document_source(metadata),
        "page": str(document_page(metadata) if document_page(metadata) is not None else "-"),
        "chunk_index": str(raw_chunk_index if raw_chunk_index is not None else "-"),
        "content_hash": short_content_hash(doc.page_content),
    }
