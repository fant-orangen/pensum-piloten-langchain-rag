# Pensum Piloten — Codebase Guide

## Project

Pensum Piloten is a RAG-based tutoring chatbot for students. Its core goal is to help students learn course material effectively, drawing on principles from educational psychology (Socratic questioning, guided discovery, spaced repetition framing). The system avoids giving direct answers and instead guides students toward understanding through targeted questions and hints.

The key retrieval technique is **KG2RAG**: a hybrid that combines a vector store (ChromaDB) with a Knowledge Graph (Neo4j) to retrieve semantically and relationally relevant context before generation.

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | Anthropic Codex (default: `Codex-sonnet-4-6`), OpenAI, or local via IDUN HPC gateway |
| RAG framework | LangChain 0.3 |
| Vector store | ChromaDB |
| Knowledge graph | Neo4j + NetworkX |
| Embeddings | `sentence-transformers` (local) or OpenAI |
| API | FastAPI + Uvicorn |
| UI | React + Vite |
| Database | PostgreSQL via SQLModel + asyncpg; migrations with Alembic |
| Auth | JWT (PyJWT) + bcrypt |
| Config | `pydantic-settings`, loaded from `.env` |
| Linting/typing | Ruff, mypy (strict) |

---

## Source layout

```
src/
  config/         Settings singleton (get_settings()), all env vars live here
  ingestion/      Document loading, chunking, TOC filtering
  vectorstore/    ChromaDB persistence and embedding wrappers
  kg/             Knowledge graph: extraction, organisation, Neo4j storage, retrieval
  retriever/      Hybrid retriever combining vector and KG results
  chain/          LangChain chains: kg_rag_chain (default), rag_chain, no_rag_chain
  prompts/        Prompt templates (Socratic tone enforced here)
  models.py       Shared pydantic domain models
  domain/         Domain objects: User, Course
  storage/        Repository layer: users_repo, courses_repo
  services/       Shared services (auth, course)
  api/
    app.py        FastAPI app entry point; /health and /ask endpoints; chain cache
    routers/      auth, conversations, courses
    models/       SQLModel DB models (User, Course, Enrollment, Conversation, Message)
    schemas/      Pydantic request/response schemas
    services/     Business logic: auth, conversations, courses, messages
    database.py   Engine init and async session factory
    security.py   JWT creation and verification
    utils/authorization_util.py  Role-based access control helpers
    dependencies.py   FastAPI dependency injection (current user, DB session)
    seed.py       Optional test data seeding (controlled by seed_test_data setting)
frontend/
  src/
    App.tsx       React Router route tree
    api/          Typed API clients for FastAPI endpoints
    contexts/     Authentication state and providers
    pages/        Route-level React pages
    components/   Shared React UI components
```

---

## Key architectural patterns

**Settings**: All configuration lives in `src/config/settings.py`. `get_settings()` returns a cached singleton. Override any value via environment variable or `.env` file at the project root.

**Chains**: The `/ask` endpoint selects a chain by `mode`. `kg_rag_chain` is the primary chain — it runs KG-expanded retrieval before generation. `no_rag_chain` is a plain LLM fallback. Chains are built lazily and cached in `_chain_cache` in `app.py`.

**Frontend state**: The React frontend keeps authentication state in `AuthContext`, server state in TanStack Query, and the JWT token in `localStorage`.

**Frontend routing**: The UI is a React single-page app. `frontend/src/App.tsx` defines protected routes for auth, dashboard, chat, teacher course pages, admin, and settings.

**API ↔ UI**: The React frontend talks to the FastAPI backend through typed clients in `frontend/src/api/`. `api/client.ts` attaches the JWT bearer token and handles unauthorized responses.

---

## Entry points and scripts

```bash
# Run the API server
serve                  # via pyproject.toml script (uvicorn on port 8000)

# Ingest documents into the vector store
ingest                 # reads data/documents/, writes to data/chroma/

# Build the knowledge graph
ingest-kg              # extracts entities/relations and loads them into Neo4j

# Run the React frontend
cd frontend
npm run dev

# Tests
pytest
```

---

## Data flow (RAG request)

1. Student sends a question from the React chat page
2. UI sends `POST /conversations/{conversation_id}/messages` with the JWT header
3. API persists the human message and invokes the course-scoped KG-RAG chain
4. `kg_rag_chain` runs: vector retrieval → KG expansion (hop out from matched chunks in Neo4j) → re-rank/merge context
5. Augmented context + Socratic prompt template → LLM
6. API stores the AI response and source references; UI displays the response and can fetch sources on demand

## Important Guidelines
1. If Codex writes a plan, that plan should be saved for later reference in ai/plans.
2. If Codex writes an important explanation or overview, or documentation provided specifically for user reference during development (not normal documentation), this should be placed in ai/docs. 
