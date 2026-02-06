"""Embedding model factory.

Centralises embedding model creation so every component (ingestion, retrieval)
uses the exact same model and dimensionality.
"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from src.config import get_settings


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    """Return a cached embedding model instance."""
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model_name,
        openai_api_key=settings.openai_api_key,
    )
