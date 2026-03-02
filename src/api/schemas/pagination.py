"""Generic pagination schemas shared across all list endpoints."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters accepted by any paginated endpoint."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    """Envelope returned by all paginated endpoints."""

    items: list[T]
    total: int       # total number of matching rows
    page: int
    page_size: int
    pages: int       # total number of pages

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        import math
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=math.ceil(total / params.page_size) if total else 0,
        )
