"""FastAPI application — thin HTTP layer over the RAG chain."""

import uvicorn
import structlog
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from src.config import get_settings
from src.chain import build_rag_chain
from src.api.schemas import AskRequest, AskResponse

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Pensum Piloten",
    description="Socratic RAG tutor that guides students toward independent learning.",
    version="0.1.0",
)

# Build the chain once at startup and reuse it across requests.
_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        _chain = build_rag_chain()
    return _chain


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Submit a student question and receive Socratic guidance."""
    chain = _get_chain()

    # Convert the flat chat history into LangChain message objects.
    history = []
    for msg in request.chat_history:
        if msg.role == "human":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))

    try:
        answer = await chain.ainvoke(
            {"question": request.question, "chat_history": history}
        )
    except Exception as exc:
        logger.error("chain_error", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to generate response.")

    # Extract source filenames from the retriever step (stored in the
    # formatted context string).  A more robust approach would capture the
    # retriever's raw documents; this is a lightweight first pass.
    sources: list[str] = []

    return AskResponse(answer=answer, sources=sources)


def start():
    """Entry-point used by ``pyproject.toml`` ``[project.scripts]``."""
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
