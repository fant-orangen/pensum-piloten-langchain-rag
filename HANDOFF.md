# Scaling Handoff

Issues blocking Pensum Piloten from serving a full student cohort. Assessed at commit
`6e62fe2`.

## 1. Uploaded course materials are not on a persistent volume

Uploads go to `/app/data/documents` (`src/config/settings.py:73`), which
`docker-compose.yml` does not mount as a volume. The files sit in the container's writable
layer and are lost when the container is recreated (`up --build`, `down` then `up`, or a
compose config change). Only applies to Compose; the host-run workflow writes to the repo
directory and persists.

Postgres rows and Chroma embeddings survive, so nothing appears broken: chat keeps
answering from the existing index and the materials tab lists files that no longer exist.
The failure surfaces at the next rebuild, when `load_documents_from_paths`
(`src/api/services/course_documents.py:822`) reads paths that are gone.

`COPY data/ data/` (`Dockerfile.backend:22`) additionally bakes a snapshot of the local
`data/` directory into every image.

**Fix:** add a named volume for `/app/data/documents`; narrow or drop the `COPY`.

## 2. Database connections are held across the LLM call, on an unsized pool

The engine is created with no pool arguments (`src/api/database.py:40`), giving
SQLAlchemy's default of 5 connections plus 10 overflow. `get_db` holds a session for the
whole request and never commits before the chain runs, so each chat request keeps a
connection checked out and idle for the 10–60s it spends in `chain.ainvoke`
(`src/api/services/messages.py:222`). Compression turns make two sequential LLM calls in
the same request (`src/api/services/conversation_context_summaries.py:105-118`).

15 concurrent chats exhaust the pool and the 16th blocks, while Postgres itself sits idle.
Nginx returns 504 past its default 60s `proxy_read_timeout`, which `nginx.conf` does not
override.

**Fix:** set explicit pool sizes, and release the session before the LLM call — load
course and history, close, invoke, reopen to persist. Requires splitting `create_message`,
which currently commits both messages in one transaction after the chain returns.

## 3. bcrypt runs on the event loop

`hash_password` and `verify_password` (`src/api/services/auth.py:12-19`) are called
synchronously from `authenticate_user` and `change_password`. Each call burns 100–300ms of
CPU holding the GIL, and the backend is a single process (`Dockerfile.backend:26`, no
`--workers`), so nothing else in the application progresses during that time. A login rush
at the start of a lecture serialises, stalling in-flight chat requests along with it.

**Fix:** call both through `asyncio.to_thread`.

## 4. Missing indexes on frequently filtered columns

- `message.conversation_id` (`src/api/models/message.py:24`)
- `conversation.user_id`, `conversation.course_id`
- `course_enrollment.course_id` — the `uq_enrollment` constraint indexes
  `(user_id, course_id)`, which does not serve lookups by course alone

Each causes a sequential scan. `message` is the largest and most-read table, and
`conversation_id` is filtered twice per chat turn: once by the history query in
`create_message`, once by `maybe_compress_conversation_history`. That history query also
has no `LIMIT`, so it returns every message in the conversation each turn — compression
bounds what reaches the LLM, not what Postgres reads.

**Fix:** add the indexes; bound the history query.

## 5. Chroma runs embedded, so only one backend process is possible

`src/vectorstore/store.py:23` uses `chromadb.PersistentClient` against a local directory —
SQLite-backed and single-writer, requiring one process to own the files. `store.py:36`
already flags this: `# TODO: should not be used in production`.

Adding `--workers N` or a second container gives multiple processes write access to the
same SQLite files and corrupts the index, so horizontal scaling is not reachable by
configuration alone.

**Fix:** run Chroma in server mode, or migrate to pgvector on the existing Postgres.

## 6. Ingestion runs in the web process with no queue or lock

Rebuilds are dispatched with FastAPI `BackgroundTasks`
(`src/api/routers/courses.py:450`), so the job exists only in the memory of the process
that served the request. Three consequences:

**Courses get stuck.** A restart or crash mid-rebuild discards the task while
`rebuild_status` stays `queued`/`building`. Nothing reconciles those rows at startup, and
chat is rejected in that state (`src/api/services/messages.py:145`), so the course is
unusable until the row is edited by hand.

**Ingestion competes with chat.** Embedding and triplet extraction run in the process
serving student requests. `extract_triplets` (`src/kg/extractor.py:99`) issues 10
concurrent LLM calls per batch with no limit shared across courses.

**Two rebuilds can start at once.** `_ensure_not_rebuilding` reads `rebuild_status` then
writes it with no row lock in between.

**Fix:** move ingestion to a task queue with its own worker, reconcile stale `building`
rows at startup, and take a `SELECT ... FOR UPDATE` on the course row.

## 7. No rate limiting or cost accounting

Nothing enforces a request rate, quota, or token budget per user, and every chat turn is a
billed LLM call. There is also no per-user or per-course token accounting, so spend cannot
be attributed after the fact.

**Fix:** rate-limit the message endpoint; record token counts per conversation.

## 8. Chat responses are not streamed

`create_message` waits for the complete answer from `chain.ainvoke`
(`src/api/services/messages.py:222`) and returns it as one JSON response — there is no
streaming anywhere in the codebase. Students see a loading state for the full 10–60s.

**Fix:** stream over SSE with `chain.astream()`. Needs `proxy_buffering off` and a raised
`proxy_read_timeout` in `nginx.conf`, plus a decision on whether to save a partial answer
when the client disconnects.

## Additional items

- **Test data seeds on every startup.** `seed_test_data` defaults to `True`
  (`src/config/settings.py:99`).
- **No migration tool.** `create_tables` (`src/api/database.py:47-180`) runs ~15 ad-hoc
  `ALTER TABLE` statements and an `UPDATE course SET rag_mode` on every boot. Concurrent
  starts would contend for `ACCESS EXCLUSIVE` locks.
- **Invalid CORS config.** `docker-compose.yml` sets `CORS_ORIGINS: '["*"]'` while
  `src/api/app.py:51` passes `allow_credentials=True`. Browsers reject that combination.
- **Unbounded chain cache.** `_chain_cache` (`src/api/services/messages.py:29`) has no
  eviction. Each rebuild adds an entry under the new scope and keeps the old chain, along
  with its unclosed Neo4j driver (`src/kg/retriever.py:369`) for `kg_rag` courses.

## Order

1. Item 1 — active data loss, two lines to fix.
2. Items 2, 3, 4 — small and independent; they raise single-process capacity.
3. Items 5 and 6 — both required before adding workers or replicas.
4. Item 7 — required before granting cohort access.
5. Item 8 — user-facing latency.
