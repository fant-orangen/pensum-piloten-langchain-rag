"""Helpers for normalizing source document metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_PAGE_KEYS = (
    "page",
    "page_label",
    "page_number",
    "page_num",
    "source_page",
    "page_index",
)
_LOC_PAGE_KEYS = (
    "page",
    "page_label",
    "pageNumber",
    "page_number",
)


def _coerce_text(value: Any) -> str:
    """Convert arbitrary metadata values to stripped display text."""

    if value is None:
        return ""
    text = str(value).strip()
    return text


def _page_from_mapping(mapping: Mapping[str, Any] | None) -> str:
    """Extract a page-like value from flat, nested metadata, or loader loc fields."""

    if mapping is None:
        return ""

    for key in _PAGE_KEYS:
        value = _coerce_text(mapping.get(key))
        if value:
            return value

    metadata = mapping.get("metadata")
    if isinstance(metadata, Mapping):
        for key in _PAGE_KEYS:
            value = _coerce_text(metadata.get(key))
            if value:
                return value

    loc = mapping.get("loc")
    if isinstance(loc, Mapping):
        for key in _LOC_PAGE_KEYS:
            value = _coerce_text(loc.get(key))
            if value:
                return value

    return ""


def extract_source_page(
    source: Mapping[str, Any] | None,
    fallback: Mapping[str, Any] | None = None,
) -> str:
    """Return the first non-empty page-like value from source/fallback metadata."""
    return _page_from_mapping(source) or _page_from_mapping(fallback)
