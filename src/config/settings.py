"""Centralised application settings loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# TODO: review these settings and evaluate whether we need to change them.
class Settings(BaseSettings):
    """All tuneable knobs live here.  Override via env vars or a .env file."""

    # --- LLM provider ---
    model_provider: str = "anthropic"  # "openai" | "anthropic" | "local"

    # --- IDUN LLM gateway (used when model_provider = "local") ---
    idun_base_url: str = "https://llm.hpc.ntnu.no/v1"
    idun_api_key: str = ""

    # --- OPENAI ---
    openai_api_key: str = Field(default="", description="OpenAI API key loaded from OPENAI_API_KEY environment variable")
    openai_llm_model: str = "gpt-5.5"
    openai_embedding_model: str = "text-embedding-3-small"

    # --- Anthropic ---
    anthropic_api_key: str = Field(default="", description="Anthropic API key loaded from ANTHROPIC_API_KEY environment variable")
    anthropic_llm_model: str = "claude-sonnet-4-6"


    # Change these if you want a different local model.
    local_llm_model: str = "moonshotai/Kimi-K2.5"
    local_embedding_model: str = "intfloat/multilingual-e5-small"

    # --- Vector store (Chroma) ---
    chroma_persist_dir: str = str(PROJECT_ROOT / "data" / "chroma")
    chroma_collection_name: str = "pensum_piloten"

    # --- Chunking ---
    chunk_size: int = 800
    chunk_overlap: int = 150

    # --- Retrieval ---
    retriever_top_k: int = 5
    reranker_candidate_k: int = 30
    reranker_top_k: int = 5
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    kg_max_final_chunks: int = 20
    temperature: float = 0.3
    conversation_compression_token_limit: int = 30000

    # --- Neo4j (Knowledge Graph) ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    kg_expansion_hops: int = 1
    kg_max_expanded_chunks: int = 10
    # kg_min_chunk_score: float = 0.5


    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/pensum_piloten"

    # --- Auth ---
    # Override with a long random string in production. Generate one with:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = "change-me-in-production"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    # Comma-separated list of allowed CORS origins (e.g. "http://localhost:5173,https://myapp.example.com")
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]

    # --- Document source directory ---
    documents_dir: str = str(PROJECT_ROOT / "data" / "documents")
    course_materials_dir: str = str(PROJECT_ROOT / "data" / "course_materials")

    # --- Ingestion filtering ---
    toc_line_threshold: float = 0.5 # If more than 50% of the lines in a document match the TOC line pattern, the document is removed.
    
    # --- LLM test generation ---
    test_chat_max_messages_per_agent: int = 12

    # --- Zip import ---
    zip_max_files: int = 500  # Maximum number of files extracted from a single zip upload.

    # --- Seeding ---
    # Set to true to insert a test course, teacher, and student on startup.
    # Safe to leave on — seed is skipped if data already exists.
    seed_test_data: bool = False

    # --- KG autoload ---
    # On API startup, replay any cached per-course KG triplets from disk into
    # Neo4j for scopes that are currently empty. Lets a fresh
    # Neo4j volume (e.g. a new Docker container) inherit the graph built by a
    # previous `ingest-kg` run without repeating extraction.
    kg_autoload_on_startup: bool = True

    # --- Optional admin bootstrap ---
    # If both email and password are set, startup ensures this account exists
    # with global_role="admin".
    admin_email: str = ""
    admin_password: str = ""
    admin_first_name: str = "System"
    admin_last_name: str = "Admin"

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
