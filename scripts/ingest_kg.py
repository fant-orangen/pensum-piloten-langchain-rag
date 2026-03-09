"""KG ingestion script — full vector + triplet + KG ingestion pipeline.

Triplets are cached to data/kg_triplets.json after extraction so they survive
crashes and can be reused by scripts/build_kg.py.

Usage:
    python -m scripts.ingest_kg                      # full pipeline
    python -m scripts.ingest_kg --dir /path/to/docs  # custom directory
"""

import argparse
import sys
from pathlib import Path

import structlog

from src.config import get_settings
from src.ingestion import run_kg_ingestion_pipeline

logger = structlog.get_logger(__name__)

_CACHE_DIR = Path(get_settings().chroma_persist_dir).parent
_TRIPLETS_CACHE = _CACHE_DIR / "kg_triplets.json"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents into vector store and build knowledge graph."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to the documents directory (defaults to settings.documents_dir).",
    )
    args = parser.parse_args(argv)

    try:
        run_kg_ingestion_pipeline(
            documents_dir=args.dir,
            triplets_cache_path=_TRIPLETS_CACHE,
        )
    except ValueError:
        logger.error("no_documents_found")
        sys.exit(1)


if __name__ == "__main__":
    main()
