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
| UI | Gradio |
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
  services/       Shared services (auth, course) used by API and UI
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
  ui/
    main_app.py   Root gr.Blocks app; assembles all pages and wires all events
    pages/        One file per page — each exports build_*_page() and handler functions
    services/     HTTP clients that call the API (api_client, auth_service, course_service, conversation_service)
    state.py      App state dict helpers (typed accessors, state mutation functions)
    router.py     Route constants and visibility update logic
```

---

## Key architectural patterns

**Settings**: All configuration lives in `src/config/settings.py`. `get_settings()` returns a cached singleton. Override any value via environment variable or `.env` file at the project root.

**Chains**: The `/ask` endpoint selects a chain by `mode`. `kg_rag_chain` is the primary chain — it runs KG-expanded retrieval before generation. `no_rag_chain` is a plain LLM fallback. Chains are built lazily and cached in `_chain_cache` in `app.py`.

**UI state**: The Gradio app uses a single flat `dict` passed through `gr.State`. All reads and writes go through typed helpers in `state.py` — never access state keys directly.

**Page pattern**: Each page in `ui/pages/` exports:
- A `build_*_page()` function returning a `*PageComponents` dataclass of Gradio components
- Pure handler functions that take state and inputs, return updated state and component values
- `main_app.py` owns all `.click()` / `.change()` event wiring

**Routing**: The UI is a single-page app. `router.py` defines route constants and a `route_visibility_updates()` function that returns `gr.update(visible=...)` for every page group. Navigation is done by mutating the route in state and re-rendering.

**API ↔ UI**: The Gradio UI talks to the FastAPI backend exclusively through `ui/services/api_client.py`. The JWT token from login is stored in `gr.State` and passed with each request.

---

## Entry points and scripts

```bash
# Run the API server
serve                  # via pyproject.toml script (uvicorn on port 8000)

# Ingest documents into the vector store
ingest                 # reads data/documents/, writes to data/chroma/

# Build the knowledge graph
ingest-kg              # extracts entities/relations and loads them into Neo4j

# Run the Gradio UI (from project root)
python -m src.ui.main_app

# Tests
pytest
```

---

## Data flow (RAG request)

1. Student sends a question from the Gradio chat page
2. UI sends `POST /ask` with `{question, chat_history, mode}` and JWT header
3. `kg_rag_chain` runs: vector retrieval → KG expansion (hop out from matched chunks in Neo4j) → re-rank/merge context
4. Augmented context + Socratic prompt template → LLM
5. LLM response streamed back; UI displays it without revealing sources directly to student

## Important Guidelines
1. If Codex writes a plan, that plan should be saved for later reference in ai/plans.
2. If Codex writes an important explanation or overview, or documentation provided specifically for user reference during development (not normal documentation), this should be placed in ai/docs. 
