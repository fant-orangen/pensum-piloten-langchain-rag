"""Admin endpoints — user listing and role promotion (admin-only)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.admin import AdminUserRead
from src.api.services.admin import list_users, promote_user_to_teacher

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserRead])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserRead]:
    """Return all users. Requires admin."""
    users = await list_users(current_user, db)
    return [AdminUserRead.model_validate(user) for user in users]


@router.post("/users/{user_id}/promote-teacher", response_model=AdminUserRead)
async def promote_to_teacher(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserRead:
    """Promote a user to global teacher role. Requires admin."""
    user = await promote_user_to_teacher(current_user, user_id, db)
    return AdminUserRead.model_validate(user)
