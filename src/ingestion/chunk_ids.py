"""Stable chunk identifiers shared by vector and KG ingestion."""

import hashlib

from langchain_core.documents import Document


def make_chunk_id(doc: Document) -> str:
    """Generate a stable, deterministic ID for a chunk based on source and position."""
    source = doc.metadata.get("source_path") or doc.metadata.get("source_file", "unknown")
    page = doc.metadata.get("page", "")
    start = doc.metadata.get("start_index", 0)
    raw = f"{source}:{page}:{start}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
