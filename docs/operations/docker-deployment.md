# Docker Deployment

Source files:

- Compose stack: `docker-compose.yml`
- Backend image: `Dockerfile.backend`
- Frontend image: `Dockerfile.frontend`
- Nginx config: `nginx.conf`

## Stack

```bash
docker compose up --build
```

Services:

| Service | Image/build | Network exposure |
|---|---|---|
| `frontend` | `Dockerfile.frontend` | Host port `80` mapped to container port `80`. |
| `backend` | `Dockerfile.backend` | Container port `8000`; no host port mapping in compose. |
| `postgres` | `postgres:16-alpine` | Internal compose network only. |
| `neo4j` | `neo4j:5-community` | Internal compose network only. |

The browser entry point is:

```text
http://localhost/
```

The frontend container's Nginx proxies API routes to `http://backend:8000`.

## Backend Container

`Dockerfile.backend`:

1. starts from `python:3.11.12-slim-bookworm`;
2. installs `gcc` and `libpq-dev`;
3. installs project dependencies from `pyproject.toml`;
4. copies backend runtime files;
5. runs Uvicorn on `0.0.0.0:8000`.

Compose passes `.env` into the backend and overrides:

| Variable | Compose value |
|---|---|
| `DATABASE_URL` | PostgreSQL service URL using the compose `postgres` host. |
| `NEO4J_URI` | `bolt://neo4j:7687` |
| `API_RELOAD` | `false` |
| `CORS_ORIGINS` | `["*"]` |

## Frontend Container

`Dockerfile.frontend`:

1. builds the Vite app with Node `20.19`;
2. copies `dist/` into Nginx `1.27`;
3. installs `nginx.conf` as the default server config.

`nginx.conf` proxies these prefixes to the backend:

- `/auth`
- `/courses`
- `/conversations`
- `/admin`
- `/preferences`
- `/health`

All other paths fall back to `/index.html` for React Router.

## Volumes

| Volume | Mounted at | Purpose |
|---|---|---|
| `pgdata` | `/var/lib/postgresql/data` | PostgreSQL data. |
| `neo4jdata` | `/data` | Neo4j data. |
| `chromadata` | `/app/data/chroma` | ChromaDB persistence. |
| `./data/course_materials` | `/app/data/course_materials:ro` | Read-only course material bind mount. |

Course material upload and rebuild workflows write files under `DOCUMENTS_DIR/<COURSE_CODE>`. With the default container settings, that path is `/app/data/documents/<COURSE_CODE>`. The compose file does not mount `/app/data/documents`, so uploaded documents are stored in the backend container filesystem and are lost when the backend container is replaced.

## Health

From the host, the proxied health endpoint is:

```bash
curl http://localhost/health
```

From inside the compose network, the backend endpoint is:

```text
http://backend:8000/health
```
