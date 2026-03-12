"""Helpers for constructing HTTP exceptions across the API layer."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


def http_error(
    status_code: int,
    detail: str | dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a FastAPI HTTPException with optional headers."""
    return HTTPException(status_code=status_code, detail=detail, headers=headers)


def bad_request_error(
    detail: str | dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a 400 Bad Request exception."""
    return http_error(status.HTTP_400_BAD_REQUEST, detail, headers=headers)


def unauthorized_error(
    detail: str | dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a 401 Unauthorized exception."""
    return http_error(status.HTTP_401_UNAUTHORIZED, detail, headers=headers)


def forbidden_error(
    detail: str | dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a 403 Forbidden exception."""
    return http_error(status.HTTP_403_FORBIDDEN, detail, headers=headers)


def not_found_error(
    detail: str | dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a 404 Not Found exception."""
    return http_error(status.HTTP_404_NOT_FOUND, detail, headers=headers)


def conflict_error(
    detail: str | dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a 409 Conflict exception."""
    return http_error(status.HTTP_409_CONFLICT, detail, headers=headers)


def stage_error(
    code: str,
    message: str,
    *,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Construct a stage-tagged error string that survives the current frontend client."""
    return http_error(status_code, f"[{code}] {message}", headers=headers)
