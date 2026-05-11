"""Shared structured logging helpers for API services."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, Literal, TypeAlias

import structlog
from structlog.typing import FilteringBoundLogger

ServiceLogger: TypeAlias = FilteringBoundLogger
LogLevel: TypeAlias = Literal["info", "warning", "error"]
CourseMaterialRebuildAction: TypeAlias = Literal["queued", "started", "complete"]
ConversationCompressionAction: TypeAlias = Literal["triggered", "completed"]

_SERVICE_COMPONENT: Final = "api_service"
_COURSE_MATERIAL_REBUILD_PREFIX: Final = "course_material_rebuild"
_CONVERSATION_COMPRESSION_PREFIX: Final = "conversation_compression"


def get_service_logger(module_name: str) -> ServiceLogger:
    """Return a service logger with stable API service context already bound."""
    service_name = module_name.rsplit(".", maxsplit=1)[-1]
    return structlog.get_logger(module_name).bind(
        component=_SERVICE_COMPONENT,
        service=service_name,
    )


def bind_log_context(logger: ServiceLogger, /, **fields: object) -> ServiceLogger:
    """Bind normalized context fields once to avoid repeating fixed values."""
    return logger.bind(**_normalize_fields(fields))


def log_chain_invocation(logger: ServiceLogger, /, **fields: object) -> None:
    """Emit the standard chain invocation event for message services."""
    _log_event(logger, "invoking_chain", **fields)


def log_course_material_rebuild(
    logger: ServiceLogger,
    action: CourseMaterialRebuildAction,
    /,
    **fields: object,
) -> None:
    """Emit a high-level course material rebuild lifecycle event."""
    _log_event(logger, f"{_COURSE_MATERIAL_REBUILD_PREFIX}_{action}", **fields)


def log_course_material_rebuild_step(
    logger: ServiceLogger,
    /,
    *,
    step: str,
    **fields: object,
) -> None:
    """Emit a standardized course material rebuild step event."""
    _log_event(logger, f"{_COURSE_MATERIAL_REBUILD_PREFIX}_step", step=step, **fields)


def log_course_material_rebuild_missing_course(
    logger: ServiceLogger,
    /,
    **fields: object,
) -> None:
    """Emit the standardized warning for missing rebuild targets."""
    _log_event(
        logger,
        f"{_COURSE_MATERIAL_REBUILD_PREFIX}_missing_course",
        level="warning",
        **fields,
    )


def log_course_material_rebuild_failed(
    logger: ServiceLogger,
    /,
    *,
    error: Exception | str,
    **fields: object,
) -> None:
    """Emit the standardized rebuild failure event."""
    _log_event(
        logger,
        f"{_COURSE_MATERIAL_REBUILD_PREFIX}_failed",
        level="error",
        error=str(error),
        **fields,
    )


def log_conversation_compression(
    logger: ServiceLogger,
    action: ConversationCompressionAction,
    /,
    **fields: object,
) -> None:
    """Emit a standardized conversation compression lifecycle event."""
    _log_event(logger, f"{_CONVERSATION_COMPRESSION_PREFIX}_{action}", **fields)


def _log_event(
    logger: ServiceLogger,
    event: str,
    /,
    *,
    level: LogLevel = "info",
    **fields: object,
) -> None:
    """Normalize log fields and emit an event at the requested level."""

    getattr(logger, level)(event, **_normalize_fields(fields))


def _normalize_fields(fields: Mapping[str, object]) -> dict[str, object]:
    """Return a copy of log fields converted to structlog-friendly primitives."""

    return {key: _normalize_value(value) for key, value in fields.items()}


def _normalize_value(value: object) -> object:
    """Normalize UUIDs, paths, mappings, and sequences recursively for JSON logs."""

    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {key: _normalize_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_value(item) for item in value]
    return value
