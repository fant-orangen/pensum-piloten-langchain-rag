# Testing

Backend development dependencies are defined in `pyproject.toml` under `[project.optional-dependencies].dev`.

Install them with:

```bash
pip install -e ".[dev]"
```

## Commands

Backend checks:

```bash
pytest
ruff check .
mypy .
```

Frontend build check:

```bash
cd frontend
npm run build
```

## Backend Test Categories

| Test type | Files | Notes |
|---|---|---|
| Unit/service tests | `tests/test_*` files using `pytest`, `pytest.mark.asyncio`, `monkeypatch`, and `tmp_path`. | Exercise service logic without a running API server. |
| Server-backed endpoint checks | `tests/test_auth.py`, `tests/test_courses.py`, `tests/test_conversations.py`, `tests/test_conversation_flow.py`. | Use `urllib` against `http://localhost:8000`. |
| Shared HTTP helpers | `tests/http_client.py` | Provides request helpers and simple pass/fail reporting for server-backed checks. |

The repository does not define a root `conftest.py` at this revision.

## Server-Backed Checks

The server-backed checks require the API server to be running on:

```text
http://localhost:8000
```

The seeded-flow checks expect `SEED_TEST_DATA=true` and seeded accounts such as `student@test.com` and `teacher@test.com`.

## Focus Areas

Current tests cover:

- authentication and forced password change;
- conversation creation, deletion, message flow, and message source resolution;
- course access and enrollment imports;
- course material rebuild cleanup and source handling;
- loader formats and chunking;
- KG/RAG chain source propagation;
- message service error handling.

When changing shared behavior, add or update tests in the nearest matching `tests/test_*.py` file.
