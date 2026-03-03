"""Gradio UI entrypoint for auth, student page, and A/B comparison.

Usage:
    python scripts/app_ui.py
    python -m scripts.app_ui
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.ui.main_app import build_main_app


def main() -> None:
    app = build_main_app()
    app.queue()
    app.launch()


if __name__ == "__main__":
    main()
