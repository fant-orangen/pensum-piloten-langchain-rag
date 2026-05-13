"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import uvicorn
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.api.database import init_engine, create_tables, get_db
from src.api.routers import admin, auth, conversations, courses, preferences
from src.api.services.admin import ensure_admin_user
from src.api.seed import seed

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database state and optional seed data for the FastAPI app."""

    init_engine()
    await create_tables()
    settings = get_settings()
    async for db in get_db():
        await ensure_admin_user(
            db,
            email=settings.admin_email,
            password=settings.admin_password,
            first_name=settings.admin_first_name,
            last_name=settings.admin_last_name,
        )
    if settings.seed_test_data:
        async for db in get_db():
            await seed(db)
    yield


app = FastAPI(
    title="Pensum Piloten",
    description="Socratic RAG tutor that guides students toward independent learning.",
    version="0.1.0",
    lifespan=lifespan,
)

settings_for_cors = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_for_cors.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(courses.router)
app.include_router(conversations.router)
app.include_router(preferences.router)


@app.get("/health")
async def health():
    """Return a minimal liveness response for deployment health checks."""

    return {"status": "ok"}


def start():
    """Entry-point used by ``pyproject.toml`` ``[project.scripts]``."""
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
