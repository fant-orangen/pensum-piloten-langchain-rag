import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.api.models.conversation import Conversation
from src.api.services import conversations as conversation_service


@pytest.mark.asyncio
async def test_delete_conversation_for_user_deletes_conversation_and_commits(monkeypatch) -> None:
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        system_prompt_mode=1,
    )
    db = AsyncMock()

    async def fake_get_conversation_for_user(
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        db_session: AsyncMock,
    ) -> Conversation:
        assert conversation_id == conversation.id
        assert user_id == conversation.user_id
        assert db_session is db
        return conversation

    monkeypatch.setattr(
        conversation_service,
        "get_conversation_for_user",
        fake_get_conversation_for_user,
    )

    await conversation_service.delete_conversation_for_user(conversation.id, conversation.user_id, db)

    db.execute.assert_not_called()
    db.delete.assert_awaited_once_with(conversation)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_conversation_for_user_does_not_mutate_on_access_error(monkeypatch) -> None:
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db = AsyncMock()

    async def fake_get_conversation_for_user(
        requested_conversation_id: uuid.UUID,
        requested_user_id: uuid.UUID,
        _db_session: AsyncMock,
    ) -> Conversation:
        assert requested_conversation_id == conversation_id
        assert requested_user_id == user_id
        raise HTTPException(status_code=403, detail="Access denied.")

    monkeypatch.setattr(
        conversation_service,
        "get_conversation_for_user",
        fake_get_conversation_for_user,
    )

    with pytest.raises(HTTPException) as exc_info:
        await conversation_service.delete_conversation_for_user(conversation_id, user_id, db)

    assert exc_info.value.status_code == 403
    db.execute.assert_not_called()
    db.delete.assert_not_called()
    db.commit.assert_not_called()
