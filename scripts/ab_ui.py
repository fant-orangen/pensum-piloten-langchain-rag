"""Standalone Gradio A/B comparison UI.

Usage:
    python scripts/ab_ui.py
    python -m scripts.ab_ui
"""

from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.ui.pages.ab_page import build_ab_app


def build_app() -> gr.Blocks:
    return build_ab_app()


def main() -> None:
    app = build_app()
    app.queue()
    app.launch()


if __name__ == "__main__":
    main()
