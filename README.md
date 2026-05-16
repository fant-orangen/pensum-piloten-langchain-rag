# Pensum Piloten

Pensum Piloten is a course-scoped RAG tutoring and chat platform for students. Teachers create courses, manage course materials, enroll students, and configure course-specific instructions. Students chat with an educational assistant that grounds answers in the material indexed for the selected course.

The assistant supports multiple tutoring styles through system prompt modes:

- Socratic: guides the student with focused questions.
- Direct: answers clearly and directly.
- Example: explains through concrete examples.

Retrieval is selected per course:

- `kg_rag`: vector retrieval from Chroma followed by Neo4j knowledge graph expansion and filtering.
- `naive_rag`: vector-only similarity retrieval from Chroma.

## Main Features

- Course-scoped conversations and source attribution.
- Teacher course administration for students, teachers, materials, and course instructions.
- Material upload with staged additions/removals and explicit rebuild confirmation.
- Versioned course material indexes using Chroma collections and Neo4j graph scopes.
- User authentication with JWT, bcrypt password hashing, and forced password-change support for imported users.
- Global roles: `student`, `teacher`, `admin`.
- Course roles: `student`, `teacher`.
- React frontend with protected routes and TanStack Query server state.
- FastAPI backend with PostgreSQL persistence via SQLModel.

## Stack

- Python 3.11+
- FastAPI, Uvicorn
- LangChain 0.3
- ChromaDB
- Neo4j
- PostgreSQL, SQLModel, asyncpg
- Anthropic or OpenAI LLM providers
- OpenAI embeddings
- React, Vite, TypeScript, Tailwind CSS, TanStack Query
- Ruff and mypy for Python checks

## Source Layout

```text
src/
  api/              FastAPI app, routers, services, schemas, models, auth, database
  chain/            KG-RAG and vector-only RAG chain builders
  config/           Settings loaded from environment and .env
  ingestion/        File loading, TOC filtering, document chunking
  kg/               Triplet extraction, Neo4j storage, KG-expanded retrieval
  naive/            Vector-only retriever
  prompts/          Base educational assistant prompt and prompt mode variants
  vectorstore/      Chroma persistence and embedding wrappers
frontend/
  src/
    api/            Typed frontend API clients
    components/     Shared UI components
    contexts/       Authentication state
    pages/          Route-level screens
tests/              Backend tests
docs/               Project documentation
```

## Runtime Flow

1. A user authenticates through the React frontend.
2. The frontend stores the JWT in `localStorage` and sends it as a Bearer token.
3. A user opens a course and creates or selects a conversation.
4. When a human message is sent, the backend loads the conversation's course.
5. The backend rejects chat if the course has no ingested materials or if materials are rebuilding.
6. The backend builds or reuses a cached RAG chain for `(rag_mode, chroma_collection)`.
7. The chain retrieves course material from Chroma, optionally expands through Neo4j, formats context, applies the selected prompt mode and course instructions, and calls the configured LLM.
8. The backend stores both the human message and AI response. AI messages include source chunk metadata.
9. The frontend can request resolved source chunks for an AI message.

## Running the Application

### Docker Compose Stack

Recommended approach. Use this workflow when Docker runs the database, graph store, backend, and frontend.

Requirements:

- Docker with Compose support is running.
- Host port `80` is available for the frontend container.
- The machine can pull Docker images and install Python/Node dependencies during the image build.

Create the environment file:

```bash
cp .env.example .env
```

Edit `.env` before starting Compose. At minimum, set:

```text
MODEL_PROVIDER=openai
OPENAI_API_KEY=<your OpenAI API key>
SECRET_KEY=<long random string>
```

`.env.example` sets `NEO4J_PASSWORD=pensumpiloten`. Keep that value for a first local run, or replace it before the first Compose startup. The same `.env` value is used to initialize Neo4j and to let the backend connect to it.

For Anthropic, set `MODEL_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` because embeddings use OpenAI.

Start the stack:

```bash
docker compose up --build
```

Compose starts PostgreSQL, Neo4j, the backend, and the frontend. Do not start separate PostgreSQL or Neo4j services for this workflow. The frontend is served on port 80 and proxies API routes to the backend container.

### Host-Run Development

Use this workflow when PostgreSQL and Neo4j are running outside the application backend process.

1. Install Python dependencies:

```bash
pip install -e ".[dev]"
```

1. Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

1. Start PostgreSQL and create the database expected by the default settings:

```bash
createdb pensum_piloten
```

If the database already exists, keep it and continue.

1. Start Neo4j and make it reachable at:

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your Neo4j password>
```

1. Create a `.env` file in the project root. At minimum, set:

```text
MODEL_PROVIDER=openai
OPENAI_API_KEY=<your OpenAI API key>
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pensum_piloten
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your Neo4j password>
SECRET_KEY=<long random string>
```

For Anthropic, set `MODEL_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` because embeddings use OpenAI.

The Compose PostgreSQL and Neo4j services are configured for the containerized backend and do not publish host ports. If you run the backend on the host, run PostgreSQL and Neo4j separately or expose the compose service ports before using the default URLs.

1. Run the backend:

```bash
serve
```

1. In a second terminal, run the frontend:

```bash
cd frontend
npm run dev
```

If the frontend is not served through the Nginx container, set `VITE_API_BASE_URL` when the backend is not available at the same origin.

1. Check the backend:

```bash
curl http://localhost:8000/health
```

## Course Materials

Teachers stage material changes in the frontend and confirm ingestion from the course materials tab. The backend builds a new course scope and swaps it in only after a successful rebuild.

## Configuration

`src/config/settings.py` is the configuration source of truth. It defines the available settings, defaults, provider selection, service URLs, storage paths, retrieval parameters, upload limits, and startup data options. Review this file before running the repo.

Settings can be overridden by environment variables or by a project-root `.env` file. Environment variable names use the uppercase form of the field name, for example `database_url` becomes `DATABASE_URL`.

Important settings include:

- `MODEL_PROVIDER`: `anthropic` or `openai`.
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`.
- `OPENAI_LLM_MODEL`, `OPENAI_INGESTION_MODEL`, `ANTHROPIC_LLM_MODEL`, `ANTHROPIC_INGESTION_MODEL`.
- `DATABASE_URL`.
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.
- `SECRET_KEY`.
- `CORS_ORIGINS`.
- `CHROMA_PERSIST_DIR`.
- `DOCUMENTS_DIR`.
- `ADMIN_EMAIL`, `ADMIN_PASSWORD` for optional admin bootstrap.

## Tests and Checks

Run backend tests:

```bash
pytest
```

Run Python linting and typing:

```bash
ruff check .
mypy .
```

Run frontend build:

```bash
cd frontend
npm run build
```

## Documentation Plan

Detailed documentation lives under `docs/`:

- `docs/architecture/`: system architecture, data model, RAG pipeline, KG2RAG, frontend.
- `docs/api/`: endpoint groups and API behavior.
- `docs/operations/`: local development, configuration, deployment, database, course materials.
- `docs/development/`: backend, frontend, testing, logging and error conventions.
- `docs/product/`: roles, student workflows, teacher workflows, admin workflows, prompt modes.
- `docs/security/`: authentication, authorization, upload safety, production hardening.

## Key Implementation Files

- `src/api/app.py`: FastAPI application entry point.
- `src/config/settings.py`: application settings.
- `src/api/database.py`: async database engine and table creation.
- `src/api/routers/`: API routes.
- `src/api/services/`: business logic.
- `src/api/models/`: SQLModel tables.
- `src/prompts/templates.py`: assistant prompt and prompt modes.
- `src/chain/kg_rag_chain.py`: KG-RAG chain.
- `src/chain/naive_rag_chain.py`: vector-only RAG chain.
- `src/kg/retriever.py`: KG-expanded retriever.
- `src/api/services/course_documents.py`: material staging and rebuild workflow.
- `frontend/src/App.tsx`: frontend route tree.
- `frontend/src/api/`: frontend API clients.
