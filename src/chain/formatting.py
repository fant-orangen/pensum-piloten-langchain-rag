"""Shared formatting helpers for RAG chain context."""

from langchain_core.documents import Document


def format_docs(docs: list[Document]) -> str:
    """Concatenate retrieved documents into a source-labelled context string."""
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "")
        header = f"[Source {i}: {source}"
        if page:
            header += f", p. {page}"
        header += "]"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)
