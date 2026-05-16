# Backend Development

Backend code lives under `src/api/`.

## Structure

| Path | Role |
|---|---|
| `src/api/app.py` | FastAPI app, startup lifecycle, middleware, router registration, health route. |
| `src/api/database.py` | Async SQLAlchemy engine, session factory, startup table creation. |
| `src/api/models/` | SQLModel table definitions. |
| `src/api/schemas/` | Pydantic request and response models. |
| `src/api/routers/` | HTTP route handlers. |
| `src/api/services/` | Business logic and database mutations. |
| `src/api/dependencies.py` | Auth and request-scoped dependency injection. |
| `src/api/security.py` | JWT creation and decoding. |
| `src/api/utils/` | Authorization, exceptions, logging helpers. |

## Route Pattern

Routers use this pattern:

1. declare HTTP path, response model, and status code;
2. resolve `current_user` through `get_current_app_user()` for normal app endpoints;
3. resolve `db` through `get_db`;
4. delegate business logic to a service function;
5. return a Pydantic schema with `model_validate()`.

`/auth/me` and `/auth/change-password` use `get_current_user()` because forced-password-change users need access to those endpoints.

## Service Pattern

Services own:

- SQL queries and commits;
- authorization helper calls;
- cross-store coordination;
- filesystem and retrieval-store side effects;
- HTTP exception construction through `src/api/utils/exception_util.py`.

Routers stay thin. They do not contain multi-step database workflows.

## Database Access

Request handlers receive `AsyncSession` from `get_db()`.

Background work that runs outside request dependency injection uses `get_session_factory()`.

Startup creates missing tables and applies compatibility DDL in `create_tables()`. The current repository does not include an Alembic migration directory.

## Schemas

Response schemas that validate SQLModel objects set:

```python
model_config = {"from_attributes": True}
```

Use separate schemas for:

- create/update request bodies;
- full read models;
- compact read models used by navigation or lists;
- paginated responses through `Page[T]`.

## Course Materials

Course material changes are staged before activation.

Relevant backend ownership:

| Concern | Source |
|---|---|
| Upload and staging | `src/api/services/course_documents.py` |
| Course material routes | `src/api/routers/courses.py` |
| File loading and chunking | `src/ingestion/` |
| ChromaDB writes | `src/vectorstore/` |
| KG extraction and Neo4j writes | `src/kg/` |

The active retrieval scope is stored on `course.chroma_collection`.

## RAG Chains

Message handling builds chains through `src/api/services/messages.py`.

| Course `rag_mode` | Builder |
|---|---|
| `kg_rag` | `build_kg_rag_chain(chroma_collection=scope, graph_scope=scope)` |
| `naive_rag` | `build_naive_rag_chain(chroma_collection=scope)` |

Chains are cached by `(rag_mode, scope)`.
