"""Model factory — the single place to swap LLM and embedding backends.

Set ``MODEL_PROVIDER`` in .env to select the backend:

    openai  — ChatOpenAI + OpenAIEmbeddings (default, requires OPENAI_API_KEY)
    anthropic — ChatAnthropic + OpenAIEmbeddings
                 (requires ANTHROPIC_API_KEY and OPENAI_API_KEY)
    local   — IDUN LLM gateway (Kimi K2.5 etc.) + HuggingFace sentence-transformers
              Requires IDUN_API_KEY and NTNU network / VPN access.

Ingestion KG extraction uses the configured provider-specific ingestion model.
"""

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from src.config import get_settings


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Return a chat model for the configured provider."""
    settings = get_settings()
    if settings.model_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_llm_model,
            openai_api_key=settings.openai_api_key,
            temperature=temperature,
        )
    if settings.model_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_llm_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=temperature,
        )
    if settings.model_provider == "local":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.local_llm_model,
            openai_api_key=settings.idun_api_key,
            base_url=settings.idun_base_url,
            temperature=temperature,
        )
    raise ValueError(
        f"Unknown model_provider: {settings.model_provider!r}. "
        "Supported values: 'openai', 'anthropic', 'local'"
    )


def get_ingestion_llm(temperature: float = 0.0) -> BaseChatModel:
    """Return the model used only for ingestion-time KG extraction."""
    settings = get_settings()

    if settings.model_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_ingestion_model,
            openai_api_key=settings.openai_api_key,
            temperature=temperature,
        )

    if settings.model_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_ingestion_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=temperature,
        )

    if settings.model_provider == "local":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.local_llm_model,
            openai_api_key=settings.idun_api_key,
            base_url=settings.idun_base_url,
            temperature=temperature,
        )

    raise ValueError(
        f"Unknown model_provider: {settings.model_provider!r}. "
        "Supported values: 'openai', 'anthropic', 'local'"
    )


@lru_cache
def get_embeddings() -> Embeddings:
    """Return a cached embedding model for the configured provider."""
    settings = get_settings()
    if settings.model_provider in {"openai", "anthropic"}:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
            timeout=60,
        )
    if settings.model_provider == "local":
        return _E5Embeddings(model_name=settings.local_embedding_model)
    raise ValueError(
        f"Unknown model_provider: {settings.model_provider!r}. "
        "Supported values: 'openai', 'anthropic', 'local'"
    )


class _E5Embeddings(Embeddings):
    """Thin wrapper around HuggingFaceEmbeddings that prepends the query/passage
    prefixes required by the multilingual-e5 model family for correct similarity scores."""

    def __init__(self, model_name: str) -> None:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        self._model = HuggingFaceEmbeddings(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed passages with the prefix expected by multilingual-e5."""

        return self._model.embed_documents([f"passage: {t}" for t in texts])

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query with the prefix expected by multilingual-e5."""

        return self._model.embed_query(f"query: {text}")
