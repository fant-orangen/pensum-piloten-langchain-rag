"""FastAPI application — thin HTTP layer over the RAG chain."""

from contextlib import asynccontextmanager
from typing import Any

import uvicorn
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

from src.config import get_settings
from src.chain import build_kg_rag_chain, build_no_rag_chain
from src.api.schemas import AskRequest, AskResponse
from src.api.database import init_engine, create_tables, get_db
from src.api.routers import admin, auth, conversations, courses, preferences
from src.api.services.admin import ensure_admin_user
from src.api.seed import seed

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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

# Build chains lazily and reuse them across requests.
_chain_cache: dict[str, Any] = {}
_CHAIN_BUILDERS = {
    "rag": build_kg_rag_chain,
    "no_rag": build_no_rag_chain,
}


def _get_chain(mode: str):
    chain = _chain_cache.get(mode)
    if chain is None:
        builder = _CHAIN_BUILDERS.get(mode)
        if builder is None:
            raise ValueError(f"Unsupported mode: {mode}")
        chain = builder()
        _chain_cache[mode] = chain
    return chain


def _extract_ask_response(result: Any) -> AskResponse:
    """Normalize legacy string chains and richer RAG chain results for /ask."""
    if not isinstance(result, dict):
        return AskResponse(answer=str(result), sources=[])

    answer = result.get("answer")
    if not isinstance(answer, str):
        answer = str(answer or "")

    sources: list[str] = []
    seen: set[str] = set()
    source_documents = result.get("source_documents", [])
    if isinstance(source_documents, list):
        for doc in source_documents:
            metadata = getattr(doc, "metadata", {})
            if not isinstance(metadata, dict):
                continue
            source = str(metadata.get("source_file") or "").strip()
            if source and source not in seen:
                sources.append(source)
                seen.add(source)

    return AskResponse(answer=answer, sources=sources)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Submit a student question and receive Socratic guidance."""
    try:
        chain = _get_chain(request.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Convert the flat chat history into LangChain message objects.
    history = []
    for msg in request.chat_history:
        if msg.role == "human":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))

    try:
        result = await chain.ainvoke(
            {
                "question": request.question,
                "chat_history": history,
                "system_prompt_mode": request.system_prompt_mode,
            }
        )
    except Exception as exc:
        logger.error("chain_error", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to generate response.")

    return _extract_ask_response(result)


def start():
    """Entry-point used by ``pyproject.toml`` ``[project.scripts]``."""
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
