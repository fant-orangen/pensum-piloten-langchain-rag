"""Centralised application settings loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables or the root .env file."""

    # -------------------------------------------------------------------------
    # Model providers
    # -------------------------------------------------------------------------
    model_provider: str = "openai"  # "openai" | "anthropic" | "local"

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key loaded from OPENAI_API_KEY.",
    )
    openai_llm_model: str = "gpt-5.5"
    openai_ingestion_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key loaded from ANTHROPIC_API_KEY.",
    )
    anthropic_llm_model: str = "claude-sonnet-4-6"
    anthropic_ingestion_model: str = "claude-sonnet-4-6"

    # Existing local-provider path. It requires further setup before use.
    idun_base_url: str = "https://llm.hpc.ntnu.no/v1"
    idun_api_key: str = ""
    local_llm_model: str = "moonshotai/Kimi-K2.5"
    local_embedding_model: str = "intfloat/multilingual-e5-small"

    # -------------------------------------------------------------------------
    # API, authentication, and bootstrap users
    # -------------------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]

    # Override with a long random value in production.
    secret_key: str = "change-me-in-production"

    # If both email and password are set, startup ensures this account exists.
    admin_email: str = ""
    admin_password: str = ""
    admin_first_name: str = "System"
    admin_last_name: str = "Admin"

    # -------------------------------------------------------------------------
    # Database and retrieval stores
    # -------------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/pensum_piloten"

    chroma_persist_dir: str = str(PROJECT_ROOT / "data" / "chroma")
    chroma_collection_name: str = "pensum_piloten"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # -------------------------------------------------------------------------
    # Course documents, chunking, and upload limits
    # -------------------------------------------------------------------------
    documents_dir: str = str(PROJECT_ROOT / "data" / "documents")
    course_materials_dir: str = str(PROJECT_ROOT / "data" / "course_materials")

    chunk_size: int = 800
    chunk_overlap: int = 150
    toc_line_threshold: float = 0.5

    document_max_file_bytes: int = 25 * 1024 * 1024
    document_max_upload_files: int = 50
    document_max_total_upload_bytes: int = 100 * 1024 * 1024
    zip_max_files: int = 500
    zip_max_archive_bytes: int = 50 * 1024 * 1024
    zip_max_uncompressed_bytes: int = 100 * 1024 * 1024
    zip_max_compression_ratio: float = 100.0

    # -------------------------------------------------------------------------
    # RAG retrieval and generation
    # -------------------------------------------------------------------------
    retriever_top_k: int = 5
    naive_rag_top_k: int = 20
    kg_expansion_hops: int = 1
    kg_max_expanded_chunks: int = 10
    kg_max_final_chunks: int = 20
    temperature: float = 0.3
    conversation_compression_token_limit: int = 1000

    # -------------------------------------------------------------------------
    # Development and test data
    # -------------------------------------------------------------------------
    seed_test_data: bool = True
    test_chat_max_messages_per_agent: int = 12

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
