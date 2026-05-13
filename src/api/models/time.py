"""Timezone-aware timestamp helpers for database models."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime
from sqlmodel import Field


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""

    return datetime.now(UTC)


def utc_timestamp_field() -> Any:
    """Return a SQLModel field for non-null timezone-aware UTC timestamps."""

    return Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
