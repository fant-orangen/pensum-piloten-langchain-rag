"""Document filtering — removes pages/sections that should not be chunked.

Currently handles:
- Table of contents pages: detected by a high fraction of lines that consist of
  text followed by dot leaders or whitespace padding and a page number, e.g.
  "1.2  Fourier Analysis .............. 42"
"""

import re

import structlog
from langchain_core.documents import Document

from src.config import get_settings

logger = structlog.get_logger(__name__)

# Matches a line that looks like a TOC entry:
#   - at least 2 chars of content
#   - 3+ dots, middle-dots, dashes, or spaces acting as leaders
#   - ends with a 1–4 digit page number (with optional trailing whitespace)
_TOC_LINE_RE = re.compile(r"^.{2,80}[\s.·•–\-]{3,}\d{1,4}\s*$")


def _is_toc_document(doc: Document) -> bool:
    """Return True when a document page resembles a table of contents."""

    settings = get_settings()
    lines = [ln.strip() for ln in doc.page_content.splitlines() if ln.strip()]
    if len(lines) < 3:
        return False
    hits = sum(1 for ln in lines if _TOC_LINE_RE.match(ln))
    return hits / len(lines) >= settings.toc_line_threshold


def remove_table_of_contents(docs: list[Document]) -> list[Document]:
    """Return *docs* with table-of-contents pages removed.

    Each dropped document is logged with its source file and page so the
    removal can be audited.
    """
    kept: list[Document] = []
    for doc in docs:
        if _is_toc_document(doc):
            logger.info(
                "toc_page_removed",
                source_file=doc.metadata.get("source_file"),
                page=doc.metadata.get("page"),
            )
        else:
            kept.append(doc)

    removed = len(docs) - len(kept)
    if removed:
        logger.info("toc_removal_complete", pages_removed=removed, pages_kept=len(kept))

    return kept
