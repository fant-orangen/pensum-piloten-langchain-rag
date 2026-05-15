# Local Development

Source files:

- Python project metadata: `pyproject.toml`
- API startup: `src/api/app.py`
- Settings: `src/config/settings.py`
- Frontend package commands: `frontend/package.json`
- Container stack: `docker-compose.yml`

## Backend

Install the Python package with development tools:

```bash
pip install -e ".[dev]"
```

Run the API:

```bash
serve
```

`serve` starts `src.api.app:start`, which runs Uvicorn with:

| Setting | Default |
|---|---|
| `API_HOST` | `0.0.0.0` |
| `API_PORT` | `8000` |
| `API_RELOAD` | `true` |

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Frontend

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run Vite:

```bash
npm run dev
```

Build the production frontend bundle:

```bash
npm run build
```

## Local Services

The backend needs PostgreSQL, Neo4j, and a configured LLM provider.

Default service URLs:

| Service | Setting | Default |
|---|---|---|
| PostgreSQL | `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/pensum_piloten` |
| Neo4j | `NEO4J_URI` | `bolt://localhost:7687` |
| ChromaDB | `CHROMA_PERSIST_DIR` | `data/chroma` |

The repository `docker-compose.yml` does not publish PostgreSQL or Neo4j ports to the host. A host-run backend cannot connect to those compose services unless ports are added to the compose file or the services are run separately.

## Course Materials

Teachers manage course materials through the frontend course materials page. The API stores staged document changes and activates them only after the rebuild succeeds.

See `docs/operations/course-materials.md` for the course material lifecycle.

## Checks

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
