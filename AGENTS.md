# Pensum Piloten — Codebase Guide

## Project

Pensum Piloten is a RAG-based tutoring chatbot for students. Its core goal is to help students learn course material effectively, drawing on principles from educational psychology (Socratic questioning, guided discovery, spaced repetition framing). The system avoids giving direct answers and instead guides students toward understanding through targeted questions and hints.

The key retrieval technique is **KG2RAG**: a hybrid that combines a vector store (ChromaDB) with a Knowledge Graph (Neo4j) to retrieve semantically and relationally relevant context before generation.

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | OpenAI or Anthropic; local/IDUN path exists but is not set up |
| RAG framework | LangChain 0.3 |
| Vector store | ChromaDB |
| Knowledge graph | Neo4j + NetworkX |
| Embeddings | `sentence-transformers` (local) or OpenAI |
| API | FastAPI + Uvicorn |
| UI | React + Vite |
| Database | PostgreSQL via SQLModel + asyncpg; table creation and compatibility DDL at startup |
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
  naive/          Vector-only naive RAG chain and retriever
  chain/          Shared chain builders and formatting helpers
  prompts/        Prompt templates (Socratic tone enforced here)
  models.py       LLM and embedding model factories
  api/
    app.py        FastAPI app entry point; /health and routers
    routers/      auth, admin, conversations, courses, preferences
    models/       SQLModel DB models (User, Course, Enrollment, Conversation, Message)
    schemas/      Pydantic request/response schemas
    services/     Business logic: auth, conversations, courses, messages
    database.py   Engine init and async session factory
    security.py   JWT creation and verification
    utils/authorization_util.py  Role-based access control helpers
    dependencies.py   FastAPI dependency injection (current user, DB session)
    seed.py       Startup test data seeding (controlled by seed_test_data setting)
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

**Chains**: Course conversations select a chain from the course's persisted `rag_mode`. `kg_rag` runs KG-expanded retrieval before generation. `naive_rag` runs plain vector similarity retrieval. Chains are built lazily and cached by `(rag_mode, chroma_collection)` in `src/api/services/messages.py`.

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
3. API persists the human message and invokes the course-scoped RAG chain selected by `Course.rag_mode`
4. `kg_rag` runs vector retrieval → KG expansion (hop out from matched chunks in Neo4j) → re-rank/merge context; `naive_rag` retrieves the top vector-similar chunks directly
5. Augmented context + Socratic prompt template → LLM
6. API stores the AI response and source references; UI displays the response and can fetch sources on demand

## Important Guidelines
1. If Codex writes a plan, that plan should be saved for later reference in ai/plans.
2. If Codex writes an important explanation or overview, or documentation provided specifically for user reference during development (not normal documentation), this should be placed in ai/docs. 
