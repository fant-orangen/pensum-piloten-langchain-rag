"""Debug retrieval pipeline for a single query and mode."""

from __future__ import annotations

import argparse
import os

from src.config import get_settings
from src.retriever.retriever import get_retriever

MODE_ENV: dict[str, dict[str, str]] = {
    "baseline": {
        "GRAPH_ENABLED": "false",
        "RERANK_ENABLED": "false",
    },
    "rerank": {
        "GRAPH_ENABLED": "false",
        "RERANK_ENABLED": "true",
    },
    "graph": {
        "GRAPH_ENABLED": "true",
        "RERANK_ENABLED": "false",
    },
    "graph_rerank": {
        "GRAPH_ENABLED": "true",
        "RERANK_ENABLED": "true",
    },
}


def _configure_mode(mode: str, *, enable_logs: bool) -> None:
    overrides = MODE_ENV[mode]
    for key, value in overrides.items():
        os.environ[key] = value
    os.environ["GRAPH_LOG"] = "true" if enable_logs else "false"
    os.environ["RERANK_LOG"] = "true" if enable_logs else "false"
    get_settings.cache_clear()


def _format_doc_id(metadata: dict[str, object]) -> str:
    source = str(metadata.get("source_file") or metadata.get("source_path") or "unknown")
    page = metadata.get("page")
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    if page is not None:
        return f"{source}:p{page}"
    return source


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Inspect retrieval diagnostics for one query.")
    parser.add_argument("--query", type=str, required=True, help="Question/query to inspect.")
    parser.add_argument(
        "--mode",
        type=str,
        default="graph_rerank",
        choices=sorted(MODE_ENV),
        help="Retrieval mode to run.",
    )
    parser.add_argument("--top-n", type=int, default=8, help="How many results to print.")
    parser.add_argument(
        "--enable-logs",
        action="store_true",
        help="Enable existing graph/rerank logs in addition to compact output.",
    )
    args = parser.parse_args(argv)

    _configure_mode(args.mode, enable_logs=args.enable_logs)
    retriever = get_retriever()
    docs = retriever.invoke(args.query)

    print(f"\nMode: {args.mode}")
    print(f"Query: {args.query}")
    print(f"Retrieved docs: {len(docs)}")

    graph_debug = next(
        (doc.metadata.get("_graph_debug") for doc in docs if isinstance(doc.metadata.get("_graph_debug"), dict)),
        None,
    )
    if isinstance(graph_debug, dict):
        seed_ids = graph_debug.get("seed_ids", [])
        selected_entities = graph_debug.get("selected_entities", [])
        graph_only_ids = graph_debug.get("graph_only_ids", [])
        adaptive_profile = graph_debug.get("adaptive_profile", "off")

        print("\nSeed chunk IDs:")
        for cid in list(seed_ids)[: args.top_n]:
            print(f"  - {cid}")

        print("\nSelected entities:")
        for ent in list(selected_entities)[: args.top_n]:
            print(f"  - {ent}")

        print("\nGraph-added chunk IDs:")
        for cid in list(graph_only_ids)[: args.top_n]:
            print(f"  - {cid}")

        print(f"\nAdaptive profile: {adaptive_profile}")
    else:
        print("\nNo graph debug metadata for this mode.")

    print("\nFinal top results:")
    for i, doc in enumerate(docs[: args.top_n], start=1):
        source = _format_doc_id(doc.metadata)
        page = doc.metadata.get("page")
        retrieval_source = doc.metadata.get("retrieval_source", "base")
        page_suffix = f", p.{page}" if page is not None else ""
        print(f"{i:>2}. [{retrieval_source}] {source}{page_suffix}")


if __name__ == "__main__":
    main()
