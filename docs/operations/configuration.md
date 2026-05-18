# Configuration

Configuration is defined in `src/config/settings.py`. Values load from environment variables and the project-root `.env` file.

## Provider Selection

`MODEL_PROVIDER` defaults to `openai`.

| `MODEL_PROVIDER` | Chat model | Embeddings | Required secrets |
|---|---|---|---|
| `openai` | `OPENAI_LLM_MODEL` | `OPENAI_EMBEDDING_MODEL` | `OPENAI_API_KEY` |
| `anthropic` | `ANTHROPIC_LLM_MODEL` | `OPENAI_EMBEDDING_MODEL` | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |

KG extraction uses `get_ingestion_llm()`:

| `MODEL_PROVIDER` | KG extraction model |
|---|---|
| `openai` | `OPENAI_INGESTION_MODEL` |
| `anthropic` | `ANTHROPIC_INGESTION_MODEL` |

The repository contains an `idun/` deployment directory and a `local` model-provider path. This path is not set up to run correctly; using it requires further setup and implementation work.

Model defaults:

| Setting | Default |
|---|---|
| `OPENAI_LLM_MODEL` | `gpt-5.5` |
| `OPENAI_INGESTION_MODEL` | `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` |
| `ANTHROPIC_LLM_MODEL` | `claude-sonnet-4-6` |
| `ANTHROPIC_INGESTION_MODEL` | `claude-sonnet-4-6` |

## Core Settings

| Setting | Default | Use |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/pensum_piloten` | PostgreSQL async SQLAlchemy connection. |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt endpoint. |
| `NEO4J_USER` | `neo4j` | Neo4j username. |
| `NEO4J_PASSWORD` | empty string | Neo4j password. |
| `CHROMA_PERSIST_DIR` | `data/chroma` | ChromaDB persistence directory. |
| `CHROMA_COLLECTION_NAME` | `pensum_piloten` | Default collection name used by vector store helpers when no course scope is supplied. |
| `DOCUMENTS_DIR` | `data/documents` | Base directory for course-code document directories. |

## Retrieval Settings

| Setting | Default | Use |
|---|---|---|
| `CHUNK_SIZE` | `800` | Character chunk size for source documents. |
| `CHUNK_OVERLAP` | `150` | Character overlap between chunks. |
| `RETRIEVER_TOP_K` | `5` | Shared retrieval top-k value. |
| `NAIVE_RAG_TOP_K` | `20` | Top-k value for `naive_rag`. |
| `KG_MAX_FINAL_CHUNKS` | `20` | Maximum final chunks passed from KG retrieval. |
| `KG_EXPANSION_HOPS` | `1` | Neo4j expansion depth. |
| `TEMPERATURE` | `0.3` | Default chat generation temperature. |
| `CONVERSATION_COMPRESSION_TOKEN_LIMIT` | `1000` | Token budget for conversation summary compression. |

## API and Auth Settings

| Setting | Default | Use |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | HS256 JWT signing key. |
| `API_HOST` | `0.0.0.0` | Uvicorn host. |
| `API_PORT` | `8000` | Uvicorn port. |
| `API_RELOAD` | `true` | Uvicorn reload flag used by `serve`. |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:4173"]` | Allowed browser origins. |

Security requirements for `SECRET_KEY`, HTTPS, CORS, and browser token storage are documented in `docs/security/`.

## Upload Limits

| Setting | Default |
|---|---|
| `DOCUMENT_MAX_FILE_BYTES` | `25 MB` |
| `DOCUMENT_MAX_UPLOAD_FILES` | `50` |
| `DOCUMENT_MAX_TOTAL_UPLOAD_BYTES` | `100 MB` |
| `ZIP_MAX_FILES` | `500` |
| `ZIP_MAX_ARCHIVE_BYTES` | `50 MB` |
| `ZIP_MAX_UNCOMPRESSED_BYTES` | `100 MB` |
| `ZIP_MAX_COMPRESSION_RATIO` | `100.0` |

Upload validation and zip handling are documented in `docs/security/upload-safety.md`.

## Startup Data Settings

| Setting | Default | Startup behavior |
|---|---|---|
| `SEED_TEST_DATA` | `true` | Runs `src/api/seed.py` after table creation when set to `true`. |
| `ADMIN_EMAIL` | empty string | Enables admin bootstrap when combined with `ADMIN_PASSWORD`. |
| `ADMIN_PASSWORD` | empty string | Password for the configured bootstrap admin. |
| `ADMIN_FIRST_NAME` | `System` | First name for a created bootstrap admin. |
| `ADMIN_LAST_NAME` | `Admin` | Last name for a created bootstrap admin. |
