"""Conversation business logic and database queries."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.schemas.pagination import PaginationParams


async def get_user_conversations(
    user_id: uuid.UUID,
    params: PaginationParams,
    db: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
) -> tuple[list[Conversation], int]:
    """Return a page of conversations for a user, ordered by most recent activity.

    Returns a (items, total) tuple so the router can build a Page response.
    """
    base = select(Conversation).where(Conversation.user_id == user_id)
    if course_id is not None:
        base = base.where(Conversation.course_id == course_id)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = count_result.scalar_one()

    result = await db.execute(
        base.order_by(Conversation.updated_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    items = list(result.scalars().all())

    return items, total


async def get_conversation_for_user(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Conversation:
    """Fetch a conversation and verify it belongs to the given user.

    Raises 404 if the conversation does not exist.
    Raises 403 if the conversation exists but belongs to a different user.
    """
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalars().first()

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    if conversation.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return conversation


async def create_conversation(
    user_id: uuid.UUID,
    course_id: uuid.UUID,
    system_prompt_mode: int,
    db: AsyncSession,
) -> Conversation:
    """Create a new conversation for a user in a course.

    Raises 404 if the course does not exist, 403 if the user is not enrolled.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id,
        )
    )
    if enrollment_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this course.")

    conversation = Conversation(
        user_id=user_id,
        course_id=course_id,
        system_prompt_mode=system_prompt_mode,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation_for_user(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete one conversation owned by the given user.

    Dependent rows are removed by database-level ON DELETE CASCADE constraints.
    """
    conversation = await get_conversation_for_user(conversation_id, user_id, db)
    await db.delete(conversation)
    await db.commit()
