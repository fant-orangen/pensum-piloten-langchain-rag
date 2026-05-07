from pathlib import Path

import pytest

from src.api.models.course import Course
from src.api.models.course_document import CourseDocument
from src.api.models.user import User
from src.api.services import course_documents


class _Chunk:
    def __init__(self) -> None:
        self.metadata: dict[str, str] = {}


class _ScalarResult:
    def __init__(self, *, first: object | None = None, all_items: list[object] | None = None):
        self._first = first
        self._all_items = [] if all_items is None else all_items

    def first(self) -> object | None:
        return self._first

    def all(self) -> list[object]:
        return self._all_items


class _ExecuteResult:
    def __init__(self, *, first: object | None = None, all_items: list[object] | None = None):
        self._scalars = _ScalarResult(first=first, all_items=all_items)

    def scalars(self) -> _ScalarResult:
        return self._scalars


class _FakeSession:
    def __init__(self, course: Course, document: CourseDocument) -> None:
        self._results = [
            _ExecuteResult(first=course),
            _ExecuteResult(all_items=[document]),
            _ExecuteResult(all_items=[document]),
        ]
        self.commits = 0

    async def execute(self, _statement: object) -> _ExecuteResult:
        return self._results.pop(0)

    def add(self, _item: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _item: object) -> None:
        return None

    async def delete(self, _item: object) -> None:
        return None


class _FakeSessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    async def __aenter__(self) -> _FakeSession:
        return self._session

    async def __aexit__(
        self,
        _exc_type: object,
        _exc: object,
        _traceback: object,
    ) -> None:
        return None


@pytest.mark.asyncio
async def test_rebuild_keeps_active_target_scope_when_post_activation_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    teacher = User(
        email="teacher@test.com",
        hashed_password="hash",
        first_name="Teach",
        last_name="Er",
        global_role="teacher",
    )
    course = Course(
        name="Algorithms",
        code="TST101",
        documents_dir=str(tmp_path),
        chroma_collection="TST101_v3",
        index_version=3,
        created_by_id=teacher.id,
    )
    document_path = tmp_path / "notes.txt"
    document_path.write_text("Course notes", encoding="utf-8")
    document = CourseDocument(
        course_id=course.id,
        original_filename="notes.txt",
        storage_path=str(document_path),
        status=course_documents.DOC_STATUS_ACTIVE,
    )
    session = _FakeSession(course, document)

    deleted_scopes: list[str] = []
    cleared_scopes: list[str] = []
    built_kg_scopes: list[str] = []

    class FakeKGStore:
        def build_kg(self, _triplets: list[object], scope: str | None = None) -> None:
            assert scope is not None
            built_kg_scopes.append(scope)

        def clear(self, scope: str | None = None) -> None:
            assert scope is not None
            cleared_scopes.append(scope)
            if scope == "TST101_v3":
                raise RuntimeError("old KG cleanup failed")

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        course_documents,
        "get_session_factory",
        lambda: lambda: _FakeSessionContext(session),
    )
    monkeypatch.setattr(course_documents, "load_documents_from_paths", lambda _paths: [object()])
    monkeypatch.setattr(course_documents, "chunk_documents", lambda _documents: [_Chunk()])
    monkeypatch.setattr(course_documents, "make_chunk_id", lambda _chunk: "chunk-1")
    monkeypatch.setattr(course_documents, "build_vectorstore", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(course_documents, "extract_triplets", lambda _chunks: [])
    monkeypatch.setattr(course_documents, "_write_course_artifacts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        course_documents, "delete_vectorstore", lambda scope: deleted_scopes.append(scope)
    )
    monkeypatch.setattr(course_documents, "KGStore", FakeKGStore)

    await course_documents.run_course_material_rebuild(course.id)

    assert course.chroma_collection == "TST101_v4"
    assert course.index_version == 4
    assert course.rebuild_status == course_documents.COURSE_REBUILD_IDLE
    assert course.rebuild_error is None
    assert session.commits == 2

    assert built_kg_scopes == ["TST101_v4"]
    assert deleted_scopes == ["TST101_v3"]
    assert cleared_scopes == ["TST101_v3"]
    assert "TST101_v4" not in deleted_scopes
    assert "TST101_v4" not in cleared_scopes
