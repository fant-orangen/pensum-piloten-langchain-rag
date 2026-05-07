import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from langchain_core.documents import Document
from sqlalchemy.exc import SQLAlchemyError

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.services import messages as message_service


class _ScalarResult:
    def __init__(self, *, first=None, all_items=None):
        self._first = first
        self._all_items = [] if all_items is None else all_items

    def first(self):
        return self._first

    def all(self):
        return self._all_items


class _ExecuteResult:
    def __init__(self, *, first=None, all_items=None):
        self._scalars = _ScalarResult(first=first, all_items=all_items)

    def scalars(self):
        return self._scalars


@pytest.mark.asyncio
async def test_create_message_returns_stage_specific_error_when_agent_response_fails(
    monkeypatch,
) -> None:
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        system_prompt_mode=1,
    )
    course = Course(
        id=conversation.course_id,
        name="Test Course",
        code="TST101",
        chroma_collection="course_scope",
        documents_dir="data/documents/test",
        created_by_id=uuid.uuid4(),
    )
    db = AsyncMock()
    db.execute.side_effect = [
        _ExecuteResult(first=course),
        _ExecuteResult(all_items=[]),
    ]

    chain = AsyncMock()
    chain.ainvoke.side_effect = RuntimeError("llm failed")

    async def _fake_compress(*_args, **_kwargs):
        return None, None, False

    monkeypatch.setattr(message_service, "_get_chain", lambda _scope: chain)
    monkeypatch.setattr(
        message_service,
        "maybe_compress_conversation_history",
        _fake_compress,
    )

    with pytest.raises(HTTPException) as exc_info:
        await message_service.create_message(conversation, "hello", "human", db)

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == (
        "[message_agent_response_failed] Failed to obtain a response from the tutor agent."
    )
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_message_rolls_back_and_returns_stage_specific_error_on_db_commit_failure(
    monkeypatch,
) -> None:
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        system_prompt_mode=1,
    )
    course = Course(
        id=conversation.course_id,
        name="Test Course",
        code="TST101",
        chroma_collection="course_scope",
        documents_dir="data/documents/test",
        created_by_id=uuid.uuid4(),
    )
    db = AsyncMock()
    db.execute.side_effect = [
        _ExecuteResult(first=course),
        _ExecuteResult(all_items=[]),
    ]
    db.add = Mock()
    db.commit.side_effect = SQLAlchemyError("db down")

    chain = AsyncMock()
    chain.ainvoke.return_value = {"answer": "answer", "source_documents": []}

    async def _fake_compress(*_args, **_kwargs):
        return None, None, False

    monkeypatch.setattr(message_service, "_get_chain", lambda _scope: chain)
    monkeypatch.setattr(
        message_service,
        "maybe_compress_conversation_history",
        _fake_compress,
    )

    with pytest.raises(HTTPException) as exc_info:
        await message_service.create_message(conversation, "hello", "human", db)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == (
        "[message_persistence_failed] Failed to save the generated conversation messages."
    )
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_message_persists_sources_from_chain_result_documents(monkeypatch) -> None:
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        system_prompt_mode=1,
    )
    course = Course(
        id=conversation.course_id,
        name="Test Course",
        code="TST101",
        chroma_collection="course_scope",
        documents_dir="data/documents/test",
        created_by_id=uuid.uuid4(),
    )
    db = AsyncMock()
    db.execute.side_effect = [
        _ExecuteResult(first=course),
        _ExecuteResult(all_items=[]),
    ]
    db.add = Mock()

    source_doc = Document(
        page_content="source content",
        metadata={
            "chunk_id": "chunk-1",
            "source_file": "notes.pdf",
            "page": 7,
        },
    )
    chain = AsyncMock()
    chain.ainvoke.return_value = {
        "answer": "answer",
        "source_documents": [source_doc],
    }

    async def _fake_compress(*_args, **_kwargs):
        return None, None, False

    monkeypatch.setattr(message_service, "_get_chain", lambda _scope: chain)
    monkeypatch.setattr(
        message_service,
        "maybe_compress_conversation_history",
        _fake_compress,
    )

    ai_msg, compression_triggered = await message_service.create_message(
        conversation,
        "hello",
        "human",
        db,
    )

    assert compression_triggered is False
    assert ai_msg.content == "answer"
    assert ai_msg.sources == [
        {
            "chunk_id": "chunk-1",
            "source_file": "notes.pdf",
            "page": "7",
        }
    ]
    chain.ainvoke.assert_awaited_once()
