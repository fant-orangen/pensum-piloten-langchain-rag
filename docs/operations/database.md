# Database Operations

Application state is stored in PostgreSQL through SQLModel and async SQLAlchemy.

Source files:

- Engine/session setup: `src/api/database.py`
- Startup hook: `src/api/app.py`
- Models: `src/api/models/`
- Seed data: `src/api/seed.py`
- Admin bootstrap: `src/api/services/admin.py`

## Startup

FastAPI startup runs these database steps:

1. `init_engine()` creates the async SQLAlchemy engine from `DATABASE_URL`.
2. `create_tables()` imports `src.api.models` and runs `SQLModel.metadata.create_all`.
3. `create_tables()` applies compatibility DDL with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` and related statements.
4. `ensure_admin_user()` creates or upgrades the configured admin account when `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set.
5. `seed()` runs when `SEED_TEST_DATA=true`.

The repository includes Alembic as a dependency but does not include an Alembic migration directory at this revision.

## Compatibility DDL

`create_tables()` applies database compatibility changes for:

- `app_user.system_prompt_mode`
- `conversation.system_prompt_mode`
- `conversation_context_summary.created_at`
- `course.course_specific_instructions`
- `course.rag_mode`
- `course.index_version`
- `course.rebuild_status`
- `course.rebuild_error`
- nullable `course.chroma_collection`
- `enrollment_import_preview.candidates_name_map`
- `app_user.must_change_password`
- timestamp columns converted from timestamp without time zone to timestamp with time zone

It also maps legacy `course.rag_mode='rag'` to `naive_rag` and drops `course_chroma_collection_key`.

## Admin Bootstrap

When both `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set:

- no existing user: create a user with `global_role="admin"`;
- existing user: set `global_role="admin"` if the role differs.

`ensure_admin_user()` also migrates legacy `global_role="superadmin"` users to `admin`.

Admin management restrictions are documented in `docs/security/authentication.md`.

## Seed Data

`SEED_TEST_DATA=true` runs `src/api/seed.py` on startup.

Seed behavior:

- creates canonical admin, teacher, student, and demo users;
- creates `TEST101` and `TEST102`;
- creates enrollments for the seeded users;
- creates course document directories;
- syncs document rows from course directories;
- reconciles seeded course scopes with persisted Chroma collections.

The seed function is idempotent for the canonical data it manages.

## Data Model

The table structure, relationships, and delete behavior are documented in `docs/architecture/data-model.md`.

## Local Connectivity

Default `DATABASE_URL` points to PostgreSQL on the host:

```text
postgresql+asyncpg://postgres:password@localhost:5432/pensum_piloten
```

The compose PostgreSQL service is not published to the host. A host-run backend cannot use compose PostgreSQL unless the compose service exposes port `5432` or `DATABASE_URL` points to another reachable PostgreSQL instance.
