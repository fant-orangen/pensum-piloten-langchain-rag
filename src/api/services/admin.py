"""Admin user management business logic."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.services.auth import hash_password
from src.api.utils.exception_util import bad_request_error, conflict_error, forbidden_error, not_found_error
from src.api.utils import require_admin
from src.config import get_settings


async def ensure_admin_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> None:
    """Ensure one configured admin account exists and migrate legacy role names."""
    # Backwards compatibility for old role naming.
    legacy_admins = await db.execute(select(User).where(User.global_role == "superadmin"))
    users_to_update = list(legacy_admins.scalars().all())
    if users_to_update:
        for legacy_user in users_to_update:
            legacy_user.global_role = "admin"
            db.add(legacy_user)
        await db.commit()

    cleaned_email = email.strip().lower()
    if not cleaned_email or not password:
        return

    result = await db.execute(select(User).where(User.email == cleaned_email))
    user = result.scalars().first()
    if user is None:
        db.add(
            User(
                email=cleaned_email,
                hashed_password=hash_password(password),
                first_name=first_name.strip() or "System",
                last_name=last_name.strip() or "Admin",
                global_role="admin",
            )
        )
        await db.commit()
        return

    if user.global_role != "admin":
        user.global_role = "admin"
        db.add(user)
        await db.commit()


async def list_users(current_user: User, db: AsyncSession) -> tuple[list[User], set[uuid.UUID]]:
    """Return all users (sorted by email) and the set of user IDs that own at least one course."""
    require_admin(current_user)
    _require_primary_admin(current_user)
    result = await db.execute(select(User).order_by(User.email))
    users = list(result.scalars().all())

    owner_result = await db.execute(select(Course.created_by_id).distinct())
    course_owner_ids = set(owner_result.scalars().all())

    return users, course_owner_ids


async def promote_user_to_teacher(
    current_user: User,
    target_user_id: uuid.UUID,
    db: AsyncSession,
) -> User:
    """Set a user's global role to teacher. Requires admin."""
    require_admin(current_user)
    _require_primary_admin(current_user)

    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalars().first()
    if target_user is None:
        raise not_found_error("User not found.")

    if target_user.global_role == "admin":
        raise bad_request_error("Cannot modify an admin user.")
    if target_user.global_role == "teacher":
        raise conflict_error("User is already a teacher.")

    target_user.global_role = "teacher"
    db.add(target_user)
    await db.commit()
    await db.refresh(target_user)
    return target_user


async def demote_teacher_to_student(
    current_user: User,
    target_user_id: uuid.UUID,
    db: AsyncSession,
) -> User:
    """Demote a teacher to student: reset global role and remove all teacher enrollments."""
    require_admin(current_user)
    _require_primary_admin(current_user)

    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalars().first()
    if target_user is None:
        raise not_found_error("User not found.")

    if target_user.global_role == "admin":
        raise bad_request_error("Cannot modify an admin user.")
    if target_user.global_role == "student":
        raise conflict_error("User is already a student.")

    await _require_not_course_owner(target_user_id, db)

    target_user.global_role = "student"
    db.add(target_user)

    await db.execute(
        delete(CourseEnrollment).where(
            CourseEnrollment.user_id == target_user_id,
            CourseEnrollment.role == "teacher",
        )
    )

    await db.commit()
    await db.refresh(target_user)
    return target_user


async def _require_not_course_owner(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Raise 409 if the user is the creator of any course."""
    result = await db.execute(
        select(Course.id).where(Course.created_by_id == user_id).limit(1)
    )
    if result.scalars().first() is not None:
        raise conflict_error(
            "Cannot demote a teacher who is the creator of a course."
        )


def _require_primary_admin(current_user: User) -> None:
    """If ADMIN_EMAIL is configured, only that admin can manage users."""
    configured_admin_email = get_settings().admin_email.strip().lower()
    if configured_admin_email and current_user.email.lower() != configured_admin_email:
        raise forbidden_error("Only the configured admin account can perform this action.")
