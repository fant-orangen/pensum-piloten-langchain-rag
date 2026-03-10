"""Run the conversation compression prompt on a saved JSON conversation log.

Usage:
    python -m scripts.test_compression data/test_logs/kg-test-2026-02-28T12-10-30.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from langchain_core.output_parsers import StrOutputParser

from src.models import get_llm
from src.prompts.templates import build_conversation_compression_prompt


def _parse_messages(payload: Any) -> list[dict[str, str]] | None:
    if isinstance(payload, dict):
        payload = payload.get("messages")

    if not isinstance(payload, list):
        return None

    messages: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            return None
        role = item.get("role")
        content = item.get("content")
        if not isinstance(role, str) or not role.strip():
            return None
        if not isinstance(content, str):
            return None
        messages.append({"role": role.strip(), "content": content})
    return messages


def _format_transcript(messages: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{message['role']}: {message['content']}"
        for message in messages
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate a compressed context summary from a JSON conversation log.",
    )
    parser.add_argument(
        "conversation_file",
        type=str,
        help="Path to a JSON file containing a conversation transcript.",
    )
    args = parser.parse_args(argv)

    path = Path(args.conversation_file)
    if not path.exists() or not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    messages = _parse_messages(payload)
    if messages is None:
        print("File is not parseable as a conversation.", file=sys.stderr)
        sys.exit(1)

    transcript = _format_transcript(messages)
    if not transcript.strip():
        print("Conversation is empty.", file=sys.stderr)
        sys.exit(1)

    chain = build_conversation_compression_prompt() | get_llm(temperature=0.0) | StrOutputParser()
    summary = chain.invoke({"conversation_history": transcript})
    print(summary.strip())


if __name__ == "__main__":
    main()
