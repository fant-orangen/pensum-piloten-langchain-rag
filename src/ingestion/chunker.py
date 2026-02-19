"""Text chunking — splits Documents into retrieval-sized pieces.

Uses RecursiveCharacterTextSplitter which is the recommended default for
most document types.  It respects natural boundaries (paragraphs, sentences)
while staying within the configured size limits.
"""

from collections import defaultdict

import structlog
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import get_settings
from src.document_identity import document_page, document_source, ensure_chunk_identity

logger = structlog.get_logger(__name__)


def _build_splitter() -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        add_start_index=True,          # record byte offset in metadata
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split a list of Documents into smaller chunks for embedding.

    Each resulting chunk inherits the metadata of its parent document and
    gains:
      - ``start_index`` from the splitter
      - deterministic ``chunk_index`` (per source/page)
      - deterministic ``chunk_id`` used for dedupe and stable vectorstore ids
    """
    splitter = _build_splitter()
    chunks = splitter.split_documents(documents)

    # Developer note:
    # chunk_id must be deterministic so re-ingest upserts the same row in Chroma
    # instead of appending duplicates.
    per_page_counters: dict[tuple[str, str], int] = defaultdict(int)
    for chunk in chunks:
        source = document_source(chunk.metadata)
        page = document_page(chunk.metadata)
        key = (source, str(page) if page is not None else "-")
        chunk_index = per_page_counters[key]
        per_page_counters[key] += 1

        chunk.metadata["chunk_index"] = chunk_index
        ensure_chunk_identity(chunk, fallback_chunk_index=chunk_index)

    logger.info(
        "chunking_complete",
        input_docs=len(documents),
        output_chunks=len(chunks),
    )
    return chunks
