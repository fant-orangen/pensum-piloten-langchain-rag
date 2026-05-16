# Secrets and Production Hardening

This document lists production-sensitive settings and deployment checks.

Source files:

- `src/config/settings.py`
- `docker-compose.yml`
- `nginx.conf`
- `src/api/app.py`
- `src/models.py`

## Required Secret Changes

| Setting | Production requirement |
|---|---|
| `SECRET_KEY` | Replace `change-me-in-production` with a long random value. |
| `DATABASE_URL` | Use production PostgreSQL credentials. |
| `NEO4J_PASSWORD` / `NEO4J_URI` | Use production Neo4j credentials and endpoint. |
| `OPENAI_API_KEY` | Set only when OpenAI models or embeddings are used. |
| `ANTHROPIC_API_KEY` | Set when Anthropic chat models are used. |
| `ADMIN_PASSWORD` | Use only for controlled admin bootstrap. |

Do not commit `.env` files containing these values.

## CORS

Default settings allow:

```text
http://localhost:5173
http://localhost:4173
```

`docker-compose.yml` overrides backend CORS with:

```yaml
CORS_ORIGINS: '["*"]'
```

Production requirement:

- replace wildcard CORS with explicit frontend origins;
- keep `allow_credentials=True` in mind when setting origins;
- do not use wildcard CORS for a student-facing deployment.

## HTTPS

The provided `nginx.conf` listens on port 80 and does not configure TLS.

Production requirement:

- terminate HTTPS at a reverse proxy or load balancer;
- redirect HTTP to HTTPS;
- send browser traffic only over HTTPS because JWTs are Bearer tokens.

## Admin Bootstrap

Startup calls `ensure_admin_user()` when `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set.

Behavior:

- creates the configured admin if missing;
- promotes an existing matching user to `admin`;
- if `ADMIN_EMAIL` is configured, only that email can use admin user-management functions.

Production requirement:

- protect `ADMIN_EMAIL` and `ADMIN_PASSWORD`;
- remove `ADMIN_PASSWORD` from the runtime environment after the first admin account is created, or replace it with a rotated value before the next deployment.

## Provider Credentials

`src/models.py` selects model clients from `model_provider`.

| `model_provider` | Required credentials |
|---|---|
| `openai` | `OPENAI_API_KEY` |
| `anthropic` | `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` for embeddings |

## Data Stores

Production data stores:

- PostgreSQL stores application data.
- Chroma stores embedded course chunks.
- Neo4j stores KG entity graph data.
- Filesystem stores uploaded course documents and rebuild artifacts.

Production requirement:

- back up PostgreSQL, Chroma, Neo4j, and uploaded course material storage together;
- restrict direct access to database, graph, vector store, and upload volumes;
- use credentials distinct from local defaults.

## Runtime Flags

| Setting | Production value |
|---|---|
| `API_RELOAD` | `false` |
| `SEED_TEST_DATA` | `false` |

`docker-compose.yml` sets `API_RELOAD=false` for the backend container. `SEED_TEST_DATA` defaults to `true` for local/demo use and must be explicitly set to `false` for production.

## Not Implemented

These production controls are not implemented in the current repository:

- database migrations directory;
- centralized audit log;
- secret manager integration;
- automated key rotation;
- rate limiting middleware;
- TLS configuration in repository Nginx config.
