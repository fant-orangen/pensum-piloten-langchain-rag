"""Unit tests for ingestion from staged course document files."""

import io
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException

from src.api.models.course import Course
from src.api.models.course_document import CourseDocument
from src.api.services import course_documents
from src.kg.extractor import Triplet


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
    def __init__(self, course: Course, documents: list[CourseDocument]) -> None:
        self._results = [
            _ExecuteResult(first=course),
            _ExecuteResult(all_items=documents),
            _ExecuteResult(all_items=documents),
        ]

    async def execute(self, _statement: object) -> _ExecuteResult:
        return self._results.pop(0)

    def add(self, _item: object) -> None:
        return None

    async def commit(self) -> None:
        return None

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


class _FakeUpload:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def read(self, _size: int = -1) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_read_upload_limited_rejects_oversized_payload() -> None:
    upload = _FakeUpload([b"abc", b"def"])

    with pytest.raises(HTTPException) as exc_info:
        await course_documents._read_upload_limited(
            upload,
            max_bytes=5,
            label="Uploaded file",
        )

    assert exc_info.value.status_code == 413


def test_extract_zip_files_rejects_excessive_total_expansion() -> None:
    archive = _zip_bytes({"large.txt": b"a" * 20})

    with pytest.raises(HTTPException) as exc_info:
        course_documents._extract_zip_files(
            archive,
            10,
            _collected=[],
            _skipped=[],
            max_file_bytes=100,
            max_total_uncompressed_bytes=10,
            max_archive_bytes=1024,
            max_compression_ratio=100,
            _total_uncompressed=[0],
        )

    assert exc_info.value.status_code == 413


def test_extract_zip_files_skips_oversized_member_without_collecting_it() -> None:
    archive = _zip_bytes({"large.txt": b"a" * 20, "small.txt": b"ok"})
    collected: list[tuple[str, bytes]] = []
    skipped: list[str] = []

    course_documents._extract_zip_files(
        archive,
        10,
        _collected=collected,
        _skipped=skipped,
        max_file_bytes=10,
        max_total_uncompressed_bytes=100,
        max_archive_bytes=1024,
        max_compression_ratio=100,
        _total_uncompressed=[0],
    )

    assert collected == [("small.txt", b"ok")]
    assert skipped == ["large.txt"]


@pytest.mark.asyncio
async def test_rebuild_uses_staged_document_files_and_versioned_scope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    course = Course(
        name="Algorithms",
        code="TST101",
        documents_dir=str(tmp_path),
        index_version=0,
        created_by_id=uuid.uuid4(),
    )
    notes_path = tmp_path / "notes.txt"
    code_path = tmp_path / "example.java"
    notes_path.write_text("alpha", encoding="utf-8")
    code_path.write_text("class Example {}", encoding="utf-8")
    documents = [
        CourseDocument(
            course_id=course.id,
            original_filename="notes.txt",
            storage_path=str(notes_path),
            status=course_documents.DOC_STATUS_ACTIVE,
        ),
        CourseDocument(
            course_id=course.id,
            original_filename="example.java",
            storage_path=str(code_path),
            status=course_documents.DOC_STATUS_PENDING_ADD,
        ),
    ]
    session = _FakeSession(course, documents)

    captured: dict[str, object] = {}

    def _load_documents_from_paths(paths: list[Path]) -> list[object]:
        captured["loaded_paths"] = [path.name for path in paths]
        return [object()]

    def _build_vectorstore(
        _chunks: list[_Chunk],
        *,
        collection_name: str | None = None,
        replace: bool = False,
    ) -> None:
        captured["collection_name"] = collection_name
        captured["replace"] = replace

    class _FakeKGStore:
        def build_kg(self, _triplets: list[Triplet], scope: str | None = None) -> None:
            captured["kg_scope"] = scope

        def close(self) -> None:
            return None

    async def _skip_cleanup(**_kwargs: object) -> None:
        return None

    monkeypatch.setattr(
        course_documents,
        "get_session_factory",
        lambda: lambda: _FakeSessionContext(session),
    )
    monkeypatch.setattr(course_documents, "load_documents_from_paths", _load_documents_from_paths)
    monkeypatch.setattr(course_documents, "chunk_documents", lambda _documents: [_Chunk()])
    monkeypatch.setattr(course_documents, "make_chunk_id", lambda _chunk: "chunk-1")
    monkeypatch.setattr(course_documents, "build_vectorstore", _build_vectorstore)
    monkeypatch.setattr(
        course_documents,
        "extract_triplets",
        lambda _chunks: [Triplet(head="a", relation="b", tail="c", chunk_id="chunk-1")],
    )
    monkeypatch.setattr(course_documents, "KGStore", _FakeKGStore)
    monkeypatch.setattr(course_documents, "_write_course_artifacts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(course_documents, "_cleanup_after_activation", _skip_cleanup)

    await course_documents.run_course_material_rebuild(course.id)

    assert sorted(captured["loaded_paths"]) == ["example.java", "notes.txt"]
    assert captured["collection_name"] == "TST101_v1"
    assert captured["kg_scope"] == "TST101_v1"
    assert captured["replace"] is True
    assert course.chroma_collection == "TST101_v1"
    assert course.index_version == 1
