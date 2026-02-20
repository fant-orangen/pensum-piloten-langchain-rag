"""Model factory — the single place to swap LLM and embedding backends.

Set ``LLM_PROVIDER`` in .env to select the backend:

    openai  — ChatOpenAI + OpenAIEmbeddings (default, requires OPENAI_API_KEY)

Additional providers will be added here as needed.
"""

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from src.config import get_settings


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Return a chat model for the configured provider."""
    settings = get_settings()
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model_name,
            openai_api_key=settings.openai_api_key,
            temperature=temperature,
        )
    # TODO: add other models here; IDUN
    raise ValueError(
        f"Unknown llm_provider: {settings.llm_provider!r}. Supported values: 'openai'"
    )


@lru_cache
def get_embeddings() -> Embeddings:
    """Return a cached embedding model for the configured provider."""
    settings = get_settings()
    if settings.llm_provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=settings.embedding_model_name,
            openai_api_key=settings.openai_api_key,
            timeout=60,
        )
    # TODO: add other models here; IDUN
    raise ValueError(
        f"Unknown llm_provider: {settings.llm_provider!r}. Supported values: 'openai'"
    )
