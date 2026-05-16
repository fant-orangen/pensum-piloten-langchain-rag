"""CLI chat — interactive conversation with the vector-only RAG chain.

Usage:
    python -m scripts.chat
    python -m scripts.chat --collection-name COURSE_v1 --mode 2
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage

from src.chain import build_naive_rag_chain

_LOG_DIR = Path("data/chat_logs")

# ANSI colour codes
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _save_log(chat_history: list[HumanMessage | AIMessage]) -> None:
    """Write the terminal chat transcript to data/chat_logs if it is non-empty."""

    if not chat_history:
        return
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _LOG_DIR / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    log = [
        {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
        for m in chat_history
    ]
    filepath.write_text(json.dumps(log, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> None:
    """Run an interactive terminal chat session against the default RAG chain."""

    parser = argparse.ArgumentParser(description="Run an interactive vector-only RAG chat.")
    parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help="Chroma collection to query. Defaults to settings.chroma_collection_name.",
    )
    parser.add_argument(
        "--mode",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Prompt mode: 1=Socratic, 2=Direct, 3=Example.",
    )
    args = parser.parse_args(argv)

    print(f"\n{_BOLD}Pensum Piloten — Vector RAG Chat{_RESET}")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    chain = build_naive_rag_chain(chroma_collection=args.collection_name)
    chat_history: list[HumanMessage | AIMessage] = []

    while True:
        try:
            user_input = input(f"{_GREEN}{_BOLD}User:{_RESET} ")
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
            }
        )
        answer = result["answer"] if isinstance(result, dict) else str(result)

        print(f"{_BLUE}{_BOLD}Tutor:{_RESET} {answer}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=answer))


if __name__ == "__main__":
    main()
