"""Async database engine and session management."""

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlmodel import SQLModel

from src.config import get_settings

logger = structlog.get_logger(__name__)

_engine = None
_session_factory = None


def init_engine() -> None:
    """Initialise the async engine and session factory from settings.

    Called once at application startup via the FastAPI lifespan hook.
    Kept separate from module-level initialisation so that settings (and
    therefore environment variables) are resolved at runtime, not at import
    time — which makes testing and CLI usage easier.
    """
    global _engine, _session_factory
    settings = get_settings()
    _engine = create_async_engine(settings.database_url, echo=False)
    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    logger.info("database_engine_initialised", url=settings.database_url)


async def create_tables() -> None:
    """Create all tables that do not already exist.
    Imports the models package first so every SQLModel table class is
    registered with the shared metadata before create_all runs.
    """
    import src.api.models  # noqa: F401 — side-effect import registers metadata

    assert _engine is not None, "Call init_engine() before create_tables()"
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE app_user "
                "ADD COLUMN IF NOT EXISTS system_prompt_mode INTEGER NOT NULL DEFAULT 1"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE conversation "
                "ADD COLUMN IF NOT EXISTS system_prompt_mode INTEGER NOT NULL DEFAULT 1"
            )
        )
    logger.info("database_tables_created")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    assert _session_factory is not None, "Call init_engine() before get_db()"
    async with _session_factory() as session:
        yield session
