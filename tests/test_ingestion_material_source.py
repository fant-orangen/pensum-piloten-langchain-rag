"""Unit tests for ingestion staging from uploaded course materials."""

from pathlib import Path
import uuid

import pytest

from src.api.models.course_material import CourseMaterial
import src.api.services.ingestion_jobs as ingestion_jobs


def _material(path: Path, name: str, content: bytes) -> CourseMaterial:
    path.write_bytes(content)
    return CourseMaterial(
        id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        uploaded_by_id=uuid.uuid4(),
        original_filename=name,
        storage_path=str(path),
        mime_type="text/plain",
        size_bytes=len(content),
    )


def test_run_pipeline_with_staged_materials_uses_material_files(monkeypatch, tmp_path: Path) -> None:
    mat_a = _material(tmp_path / "a.txt", "a.txt", b"alpha")
    mat_b = _material(tmp_path / "b.java", "b.java", b"class B {}")

    captured: dict[str, object] = {}

    def _fake_run_kg_ingestion_pipeline(
        *,
        documents_dir: str | Path | None = None,
        collection_name: str | None = None,
        course_scope: str | None = None,
        triplets_cache_path: str | Path | None = None,
    ) -> dict[str, int]:
        del triplets_cache_path
        staged_root = Path(str(documents_dir))
        captured["documents_dir"] = staged_root
        captured["collection_name"] = collection_name
        captured["course_scope"] = course_scope
        captured["staged_files"] = sorted(path.name for path in staged_root.iterdir())
        return {"chunks": 2, "triplets": 1}

    monkeypatch.setattr(ingestion_jobs, "run_kg_ingestion_pipeline", _fake_run_kg_ingestion_pipeline)

    result = ingestion_jobs._run_pipeline_with_staged_materials(
        [mat_a, mat_b],
        collection_name="course_collection",
    )

    staged_files = captured["staged_files"]
    assert isinstance(staged_files, list)
    assert len(staged_files) == 2
    assert any(str(mat_a.id) in name and name.endswith("_a.txt") for name in staged_files)
    assert any(str(mat_b.id) in name and name.endswith("_b.java") for name in staged_files)
    assert captured["collection_name"] == "course_collection"
    assert captured["course_scope"] == "course_collection"
    assert result == {"chunks": 2, "triplets": 1}


def test_run_pipeline_with_staged_materials_raises_when_no_usable_files(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.txt"
    material = CourseMaterial(
        id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        uploaded_by_id=uuid.uuid4(),
        original_filename="missing.txt",
        storage_path=str(missing_path),
        mime_type="text/plain",
        size_bytes=5,
    )

    with pytest.raises(ValueError, match="No readable material files found for ingestion"):
        ingestion_jobs._run_pipeline_with_staged_materials(
            [material],
            collection_name="course_collection",
        )
