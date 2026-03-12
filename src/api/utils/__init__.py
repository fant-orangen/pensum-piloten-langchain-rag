"""Utility helpers for the API layer."""

from src.api.utils.authorization_util import (
    require_admin,
    require_course_owner_or_admin,
    require_course_teacher_or_admin,
    require_teacher_or_admin,
    require_unenroll_permission,
)
from src.api.utils.logging_util import (
    bind_log_context,
    get_service_logger,
    log_chain_invocation,
    log_course_material_rebuild,
    log_course_material_rebuild_failed,
    log_course_material_rebuild_missing_course,
    log_course_material_rebuild_step,
)

__all__ = [
    "bind_log_context",
    "get_service_logger",
    "log_chain_invocation",
    "log_course_material_rebuild",
    "log_course_material_rebuild_failed",
    "log_course_material_rebuild_missing_course",
    "log_course_material_rebuild_step",
    "require_admin",
    "require_course_owner_or_admin",
    "require_course_teacher_or_admin",
    "require_teacher_or_admin",
    "require_unenroll_permission",
]
