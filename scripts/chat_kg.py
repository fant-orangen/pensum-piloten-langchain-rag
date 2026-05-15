"""CLI chat with KG-RAG — interactive conversation using knowledge graph-expanded retrieval.

Usage:
    python -m scripts.chat_kg
    python -m scripts.chat_kg --collection-name COURSE_v1 --graph-scope COURSE_v1
    python -m scripts.chat_kg --debug   # print retrieved chunks before each response
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage

from src.chain.kg_rag_chain import build_kg_rag_chain

_LOG_DIR = Path("data/chat_logs")

# ANSI colour codes
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


class _ChunkDebugHandler(BaseCallbackHandler):
    """Callback that prints retrieved chunks to stdout."""

    def on_retriever_end(self, documents: list[Document], **kwargs: Any) -> None:
        """Print retrieved documents after a retriever run in debug mode."""

        print(f"\n{_YELLOW}{_BOLD}[DEBUG] Retrieved {len(documents)} chunk(s):{_RESET}")
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source_path") or doc.metadata.get("source_file", "unknown")
            chunk_id = doc.metadata.get("chunk_id", "?")
            page = doc.metadata.get("page", "")
            page_str = f", p. {page}" if page else ""
            print(f"\n  {_BOLD}#{i}{_RESET} {_DIM}{source} [{chunk_id}]{page_str}{_RESET}")
            print(f"{_DIM}{'─' * 60}{_RESET}")
            print(doc.page_content)
            print(f"{_DIM}{'─' * 60}{_RESET}")
        print()


def _save_log(chat_history: list[HumanMessage | AIMessage]) -> None:
    """Write the KG chat transcript to data/chat_logs if it is non-empty."""

    if not chat_history:
        return
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _LOG_DIR / f"kg-{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    log = [
        {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
        for m in chat_history
    ]
    filepath.write_text(json.dumps(log, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> None:
    """Run an interactive terminal chat session against the KG-RAG chain."""

    parser = argparse.ArgumentParser(description="Run an interactive KG-RAG chat.")
    parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help="Chroma collection to query. Defaults to settings.chroma_collection_name.",
    )
    parser.add_argument(
        "--graph-scope",
        type=str,
        default=None,
        help="Neo4j graph scope to query. Defaults to the unscoped graph.",
    )
    parser.add_argument(
        "--mode",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Prompt mode: 1=Socratic, 2=Direct, 3=Example.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print retrieved chunks before each response.",
    )
    args = parser.parse_args(argv)

    print(f"\n{_BOLD}Pensum Piloten — KG-RAG Chat{_RESET}")
    if args.debug:
        print(f"{_YELLOW}[DEBUG mode enabled — retrieved chunks will be shown]{_RESET}")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    chain = build_kg_rag_chain(
        chroma_collection=args.collection_name,
        graph_scope=args.graph_scope,
    )
    chat_history: list[HumanMessage | AIMessage] = []
    callbacks = [_ChunkDebugHandler()] if args.debug else []

    while True:
        try:
            # Print a styled label separately so readline gets a plain prompt.
            # Passing ANSI escapes directly to input() can break cursor/wrap math.
            print(f"{_GREEN}{_BOLD}User:{_RESET} ", end="", flush=True)
            user_input = input()
        except (EOFError, KeyboardInterrupt):
            _save_log(chat_history)
            print("\nGoodbye!")
            sys.exit(0)

        if user_input.strip().lower() in {"quit", "exit", "q"}:
            _save_log(chat_history)
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        result = chain.invoke(
            {
                "question": user_input,
                "chat_history": chat_history,
                "system_prompt_mode": args.mode,
                "course_specific_instructions": None,
                "conversation_summary": None,
            },
            config={"callbacks": callbacks},
        )
        answer = result["answer"] if isinstance(result, dict) else str(result)

        print(f"{_BLUE}{_BOLD}Tutor:{_RESET} {answer}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=answer))


if __name__ == "__main__":
    main()
