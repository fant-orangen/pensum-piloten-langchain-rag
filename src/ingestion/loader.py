"""Document loading — converts raw files into LangChain Document objects."""

from pathlib import Path

import structlog
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    BSHTMLLoader,
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)

from src.config import get_settings
from src.ingestion.filter import remove_table_of_contents

logger = structlog.get_logger(__name__)

# Map file extensions to the LangChain loader class that can handle them.
_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".rst",
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".xml",
    ".sql",
    ".py",
    ".java",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".go",
    ".rs",
    ".kt",
    ".swift",
    ".php",
    ".rb",
    ".sh",
    ".css",
    ".scss",
    ".sass",
    ".ini",
    ".cfg",
    ".conf",
    ".toml",
    ".log",
}
_LOADER_MAP: dict[str, type] = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".html": BSHTMLLoader,
    ".htm": BSHTMLLoader,
    **{ext: TextLoader for ext in sorted(_TEXT_EXTENSIONS)},
}

def load_single_file(file_path: Path) -> list[Document]:
    """Load a single file and return its pages / sections as Documents."""
    suffix = file_path.suffix.lower()
    loader_cls = _LOADER_MAP.get(suffix)
    if loader_cls is None:
        logger.warning("unsupported_file_type", path=str(file_path), suffix=suffix)
        return []

    logger.info("loading_file", path=str(file_path))
    loader = loader_cls(str(file_path))
    docs = loader.load()

    # Enrich metadata so we can trace chunks back to their source.
    for doc in docs:
        doc.metadata["source_file"] = file_path.name
        doc.metadata["source_path"] = str(file_path)

    return docs


def load_documents(directory: str | Path | None = None) -> list[Document]:
    """Walk *directory* and load every supported file into Documents.

    Falls back to the ``documents_dir`` from settings when no path is given.
    """
    settings = get_settings()
    root = Path(directory) if directory else Path(settings.documents_dir)

    if not root.exists():
        logger.error("documents_directory_missing", path=str(root))
        return []

    all_docs: list[Document] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in _LOADER_MAP:
            all_docs.extend(load_single_file(path))

    all_docs = remove_table_of_contents(all_docs)
    logger.info("documents_loaded", total=len(all_docs))
    return all_docs
