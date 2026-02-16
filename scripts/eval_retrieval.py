"""Evaluate retrieval quality across baseline/rerank/graph modes."""

from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
import structlog

from src.config import get_settings
from src.retriever.retriever import get_retriever

PROJECT_ROOT = Path(__file__).resolve().parents[1]
logger = structlog.get_logger(__name__)

MODE_ENV: dict[str, dict[str, str]] = {
    "baseline": {
        "GRAPH_ENABLED": "false",
        "RERANK_ENABLED": "false",
    },
    "rerank_only": {
        "GRAPH_ENABLED": "false",
        "RERANK_ENABLED": "true",
    },
    "graph_only": {
        "GRAPH_ENABLED": "true",
        "RERANK_ENABLED": "false",
    },
    "graph_rerank": {
        "GRAPH_ENABLED": "true",
        "RERANK_ENABLED": "true",
    },
}


@dataclass(slots=True)
class EvalExample:
    id: str
    question: str
    expected_source_contains: list[str]
    expected_chunk_hints: list[str]


def _set_deterministic_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np  # type: ignore[import-not-found]

        np.random.seed(seed)
    except Exception:
        pass

    try:
        import torch  # type: ignore[import-not-found]

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def _load_examples(path: Path, *, limit: int | None = None) -> list[EvalExample]:
    rows: list[EvalExample] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        payload = json.loads(raw)
        rows.append(
            EvalExample(
                id=str(payload["id"]),
                question=str(payload["question"]),
                expected_source_contains=[str(v) for v in payload.get("expected_source_contains", [])],
                expected_chunk_hints=[str(v) for v in payload.get("expected_chunk_hints", [])],
            )
        )

    if limit is not None:
        return rows[:limit]
    return rows


def _is_relevant(doc: Document, example: EvalExample) -> bool:
    source_blob = " ".join(
        str(doc.metadata.get(key, ""))
        for key in ("source_file", "source_path", "chunk_id")
    ).lower()
    content_blob = (str(doc.metadata.get("chunk_id", "")) + " " + doc.page_content).lower()

    if example.expected_source_contains:
        for hint in example.expected_source_contains:
            if hint.lower() in source_blob:
                return True
    if example.expected_chunk_hints:
        for hint in example.expected_chunk_hints:
            if hint.lower() in content_blob:
                return True
    return False


def _find_rank(docs: list[Document], example: EvalExample, *, rank_cutoff: int) -> int | None:
    for i, doc in enumerate(docs[:rank_cutoff], start=1):
        if _is_relevant(doc, example):
            return i
    return None


def _configure_mode(mode: str) -> None:
    overrides = MODE_ENV[mode]
    for key, value in overrides.items():
        os.environ[key] = value
    os.environ["GRAPH_LOG"] = "false"
    os.environ["RERANK_LOG"] = "false"
    get_settings.cache_clear()


def _evaluate_mode(
    mode: str,
    examples: list[EvalExample],
    *,
    rank_cutoff: int,
) -> tuple[dict[str, float | int], dict[str, int | None], list[dict[str, str]]]:
    _configure_mode(mode)
    retriever = get_retriever()

    ranks: dict[str, int | None] = {}
    errors: list[dict[str, str]] = []
    for example in examples:
        try:
            docs = retriever.invoke(example.question)
            ranks[example.id] = _find_rank(docs, example, rank_cutoff=rank_cutoff)
        except Exception as exc:
            logger.error(
                "eval_query_failed",
                mode=mode,
                example_id=example.id,
                error=str(exc),
            )
            ranks[example.id] = None
            errors.append({"id": example.id, "error": str(exc)})

    total = len(examples)
    hit1 = sum(1 for rank in ranks.values() if rank is not None and rank <= 1) / total
    hit3 = sum(1 for rank in ranks.values() if rank is not None and rank <= 3) / total
    hit5 = sum(1 for rank in ranks.values() if rank is not None and rank <= 5) / total
    mrr = sum((1.0 / rank) for rank in ranks.values() if rank is not None) / total

    metrics: dict[str, float | int] = {
        "hit@1": round(hit1, 4),
        "hit@3": round(hit3, 4),
        "hit@5": round(hit5, 4),
        "mrr": round(mrr, 4),
        "evaluated_examples": total,
        "matches_found": sum(1 for rank in ranks.values() if rank is not None),
        "errors": len(errors),
    }
    return metrics, ranks, errors


def _print_summary(results: dict[str, dict[str, float | int]]) -> None:
    print("\nRetrieval evaluation summary")
    print("-" * 72)
    print(f"{'mode':<14} {'hit@1':>8} {'hit@3':>8} {'hit@5':>8} {'mrr':>8} {'match':>10}")
    for mode in ("baseline", "rerank_only", "graph_only", "graph_rerank"):
        metrics = results[mode]
        print(
            f"{mode:<14} "
            f"{metrics['hit@1']:>8} {metrics['hit@3']:>8} {metrics['hit@5']:>8} "
            f"{metrics['mrr']:>8} {str(metrics['matches_found']) + '/' + str(metrics['evaluated_examples']):>10}"
        )
    print("-" * 72)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval modes on a benchmark set.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "data" / "eval" / "retrieval_eval.jsonl",
        help="Path to retrieval benchmark JSONL.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "eval" / "last_report.json",
        help="Path to write JSON report.",
    )
    parser.add_argument(
        "--rank-cutoff",
        type=int,
        default=20,
        help="Only ranks within this cutoff count for MRR/hits.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of examples to evaluate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic seed.",
    )
    args = parser.parse_args(argv)

    _set_deterministic_seed(args.seed)
    examples = _load_examples(args.dataset, limit=args.limit)
    if not examples:
        raise SystemExit(f"No eval examples found in {args.dataset}")

    results: dict[str, dict[str, float | int]] = {}
    per_example: list[dict[str, Any]] = []
    rank_by_mode: dict[str, dict[str, int | None]] = {}
    errors_by_mode: dict[str, list[dict[str, str]]] = {}

    for mode in ("baseline", "rerank_only", "graph_only", "graph_rerank"):
        metrics, ranks, errors = _evaluate_mode(mode, examples, rank_cutoff=args.rank_cutoff)
        results[mode] = metrics
        rank_by_mode[mode] = ranks
        errors_by_mode[mode] = errors

    for example in examples:
        per_example.append(
            {
                "id": example.id,
                "question": example.question,
                "ranks": {mode: rank_by_mode[mode][example.id] for mode in rank_by_mode},
            }
        )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(args.dataset),
        "rank_cutoff": args.rank_cutoff,
        "seed": args.seed,
        "evaluated_examples": len(examples),
        "modes": results,
        "errors_by_mode": errors_by_mode,
        "per_example": per_example,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    _print_summary(results)
    print(f"Report written to: {args.output}")


if __name__ == "__main__":
    main()
