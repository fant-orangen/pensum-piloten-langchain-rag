"""Tests for extended ingestion loader format support."""

from pathlib import Path

from src.ingestion.loader import load_documents


def test_load_documents_supports_code_and_html_formats(tmp_path: Path) -> None:
    (tmp_path / "lesson.java").write_text("public class Lesson {}", encoding="utf-8")
    (tmp_path / "lesson.html").write_text(
        "<html><body><h1>Lesson</h1><p>Content</p></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "lesson.md").write_text("# Lesson", encoding="utf-8")

    docs = load_documents(tmp_path)
    source_files = {doc.metadata.get("source_file") for doc in docs}

    assert "lesson.java" in source_files
    assert "lesson.html" in source_files
    assert "lesson.md" in source_files


def test_load_documents_skips_unsupported_extension(tmp_path: Path) -> None:
    (tmp_path / "supported.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "unsupported.exe").write_bytes(b"\x00\x01")

    docs = load_documents(tmp_path)
    source_files = {doc.metadata.get("source_file") for doc in docs}

    assert "supported.txt" in source_files
    assert "unsupported.exe" not in source_files
