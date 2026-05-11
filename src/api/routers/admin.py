"""Admin endpoints — user listing and role promotion (admin-only)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_app_user
from src.api.models.user import User
from src.api.schemas.admin import AdminUserRead
from src.api.services.admin import demote_teacher_to_student, list_users, promote_user_to_teacher

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserRead])
async def get_users(
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserRead]:
    """Return all users with course-owner protection metadata.

    Args:
        current_user: Authenticated caller; must be an admin.
        db: Request-scoped database session.

    Raises:
        403: Caller is not an admin.
    """
    users, course_owner_ids = await list_users(current_user, db)
    result = []
    for user in users:
        entry = AdminUserRead.model_validate(user)
        entry.is_course_owner = user.id in course_owner_ids
        result.append(entry)
    return result


@router.post("/users/{user_id}/promote-teacher", response_model=AdminUserRead)
async def promote_to_teacher(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserRead:
    """Promote a user to global teacher role.

    Args:
        user_id: User to promote.
        current_user: Authenticated caller; must be an admin.
        db: Request-scoped database session.

    Raises:
        403: Caller is not an admin.
        404: User does not exist.
    """
    user = await promote_user_to_teacher(current_user, user_id, db)
    return AdminUserRead.model_validate(user)


@router.post("/users/{user_id}/demote-student", response_model=AdminUserRead)
async def demote_to_student(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserRead:
    """Demote a teacher to student and remove teacher course enrollments.

    Args:
        user_id: Teacher to demote.
        current_user: Authenticated caller; must be an admin.
        db: Request-scoped database session.

    Raises:
        403: Caller is not an admin.
        404: User does not exist.
        409: Teacher owns courses that must be reassigned first.
    """
    user = await demote_teacher_to_student(current_user, user_id, db)
    return AdminUserRead.model_validate(user)
