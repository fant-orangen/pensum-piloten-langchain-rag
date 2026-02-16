"""CLI chat — interactive conversation with selectable teaching modes.

Usage:
    python -m scripts.chat
    python -m scripts.chat --mode socratic
    python -m scripts.chat --mode structured_instructor
    python -m scripts.chat --mode active_recall
"""

from __future__ import annotations

import argparse
import sys

from langchain_core.messages import AIMessage, HumanMessage

from src.chain import build_rag_chain
from src.prompts import normalise_teaching_mode

# ANSI colour codes
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_RESET = "\033[0m"
_BOLD = "\033[1m"

_MODE_LABELS: dict[str, str] = {
    "socratic": "Socratic Tutor",
    "structured_instructor": "Structured Direct Instructor",
    "active_recall": "Active Recall Trainer",
}


def _pick_mode_interactively() -> str:
    print("Choose learning mode:")
    print("  1) Socratic Tutor (guiding questions)")
    print("  2) Structured Direct Instructor (clear explanations)")
    print("  3) Active Recall Trainer (retrieval practice)")
    while True:
        raw = input("Select mode [1]: ").strip()
        choice = raw or "1"
        try:
            return normalise_teaching_mode(choice)
        except ValueError:
            print("Invalid choice. Use 1, 2, or 3.")


def _resolve_mode(cli_mode: str | None) -> str:
    if cli_mode:
        return normalise_teaching_mode(cli_mode)
    return _pick_mode_interactively()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chat with the RAG tutor.")
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        help=(
            "Teaching mode: socratic, structured_instructor, or active_recall. "
            "If omitted, you will be asked at launch."
        ),
    )
    args = parser.parse_args(argv)

    mode = _resolve_mode(args.mode)
    mode_label = _MODE_LABELS.get(mode, mode)
    print(f"\n{_BOLD}Pensum Piloten — {mode_label}{_RESET}")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    chain = build_rag_chain(teaching_mode=mode)
    chat_history: list[HumanMessage | AIMessage] = []

    while True:
        try:
            user_input = input(f"{_GREEN}{_BOLD}User:{_RESET} ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if user_input.strip().lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        answer = chain.invoke({"question": user_input, "chat_history": chat_history})

        print(f"{_BLUE}{_BOLD}Tutor:{_RESET} {answer}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=answer))


if __name__ == "__main__":
    main()
