"""Centralised application settings loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All tuneable knobs live here.  Override via env vars or a .env file."""

    # --- LLM ---
    openai_api_key: str = Field(default="", description="OpenAI API key loaded from OPENAI_API_KEY environment variable")
    llm_model_name: str = "gpt-4o-mini"
    embedding_model_name: str = "text-embedding-3-small"

    # --- Vector store (Chroma) ---
    chroma_persist_dir: str = str(PROJECT_ROOT / "data" / "chroma")
    chroma_collection_name: str = "pensum_piloten"

    # --- Chunking ---
    chunk_size: int = 800
    chunk_overlap: int = 150

    # --- Retrieval ---
    retriever_top_k: int = 5

    # --- Reranking ---
    rerank_enabled: bool = False
    rerank_fetch_k: int = 25          # retrieve this many candidates from Chroma
    rerank_top_k: int = 5             # keep this many after reranking (usually = retriever_top_k)
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- Graph-guided retrieval ---
    graph_enabled: bool = False
    graph_hops: int = 1
    graph_seed_k: int = 25
    graph_max_candidates: int = 60
    graph_min_entity_df: int = 2
    graph_max_entity_df: int = 200
    graph_max_entities_per_query: int = 30
    graph_index_path: str = str(PROJECT_ROOT / "data" / "graph" / "graph_index.json")

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Document source directory ---
    documents_dir: str = str(PROJECT_ROOT / "data" / "documents")

    # --- Debug / Logging ---
    rerank_log: bool = False
    rerank_log_top_n: int = 8
    rerank_log_preview_chars: int = 120
    graph_log: bool = False
    graph_log_top_n: int = 8
    graph_log_preview_chars: int = 120

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
