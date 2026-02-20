"""Centralised application settings loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All tuneable knobs live here.  Override via env vars or a .env file."""

    # --- LLM provider ---
    llm_provider: str = "openai"  # "openai" | "local"

    # --- IDUN LLM gateway (used when llm_provider = "local") ---
    idun_base_url: str = "https://llm.hpc.ntnu.no/v1"
    idun_api_key: str = ""

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

    # --- Neo4j (Knowledge Graph) ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    kg_expansion_hops: int = 1
    kg_max_expanded_chunks: int = 10
    kg_min_chunk_score: float = 0.5

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Document source directory ---
    documents_dir: str = str(PROJECT_ROOT / "data" / "documents")

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
