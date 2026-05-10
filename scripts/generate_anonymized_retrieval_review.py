"""Generate anonymized answer/chunk review material for retrieval variants.

Usage:
    python -m scripts.generate_anonymized_retrieval_review \
        --input data/questions.txt \
        --chroma-collection TEST101_v5 \
        --output-dir data/retrieval_review

Use ``--skip-generation`` to export retrieved chunks only without calling the
generator LLM.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

MethodName = Literal["vector_rag", "reranked_rag", "kg_rag"]

_QUESTION_PATTERN = re.compile(r"(?ms)^\s*(\d+)[.)]\s+(.+?)(?=^\s*\d+[.)]\s+|\Z)")
_DEFAULT_METHODS: tuple[MethodName, ...] = ("vector_rag", "reranked_rag", "kg_rag")


@dataclass(frozen=True, slots=True)
class ReviewQuestion:
    query_id: str
    question: str


@dataclass(frozen=True, slots=True)
class ReviewChunk:
    rank: int
    chunk_id: str
    document_id: str
    source: str
    page: str
    text: str
    score: float | None
    score_type: str


@dataclass(frozen=True, slots=True)
class MethodReview:
    query_id: str
    method: MethodName
    anonymous_label: str
    answer: str
    chunks: list[ReviewChunk]
    retrieval_latency_seconds: float
    generation_latency_seconds: float | None


def parse_questions(path: Path) -> list[ReviewQuestion]:
    """Load questions from JSON or numbered plain text."""
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(raw_text)
        if not isinstance(payload, list):
            raise ValueError("JSON question input must be a list.")
        questions: list[ReviewQuestion] = []
        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Question entry {index} must be an object.")
            question = str(item.get("question", "")).strip()
            if not question:
                raise ValueError(f"Question entry {index} is missing 'question'.")
            query_id = str(item.get("id") or f"q{index}").strip()
            questions.append(ReviewQuestion(query_id=query_id, question=question))
        return questions

    questions = []
    for match in _QUESTION_PATTERN.finditer(raw_text):
        number = int(match.group(1))
        question = " ".join(match.group(2).split())
        if question:
            questions.append(ReviewQuestion(query_id=f"q{number}", question=question))
    if not questions:
        raise ValueError(f"No numbered questions found in {path}.")
    return questions


def parse_methods(raw_methods: str) -> list[MethodName]:
    """Parse a comma-separated method list."""
    methods: list[MethodName] = []
    valid_methods = set(_DEFAULT_METHODS)
    for raw_method in raw_methods.split(","):
        method = raw_method.strip()
        if not method:
            continue
        if method not in valid_methods:
            raise ValueError(
                f"Unsupported method {method!r}. Expected one of: {', '.join(_DEFAULT_METHODS)}."
            )
        methods.append(cast(MethodName, method))
    if not methods:
        raise ValueError("At least one method must be selected.")
    return methods


def build_anonymous_labels(
    methods: list[MethodName],
    *,
    seed: int | None,
    query_id: str,
) -> dict[MethodName, str]:
    """Return a deterministic per-query method-to-label mapping."""
    rng = random.Random(f"{seed}:{query_id}")
    shuffled_methods = list(methods)
    rng.shuffle(shuffled_methods)
    return {
        method: f"Method {chr(ord('A') + index)}"
        for index, method in enumerate(shuffled_methods)
    }


def retrieve_documents(
    *,
    method: MethodName,
    question: str,
    chroma_collection: str,
    graph_scope: str | None,
) -> tuple[list[Any], float]:
    """Retrieve documents for one method and return documents plus latency."""
    start = time.perf_counter()
    if method == "vector_rag":
        from langchain_core.documents import Document

        from src.config import get_settings
        from src.vectorstore.store import get_vectorstore

        vectorstore = get_vectorstore(chroma_collection)
        pairs = vectorstore.similarity_search_with_score(
            question,
            k=get_settings().retriever_top_k,
        )
        docs = [
            Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "vector_distance": float(score)},
            )
            for doc, score in pairs
        ]
        return docs, time.perf_counter() - start
    elif method == "reranked_rag":
        from src.retriever import get_reranked_retriever

        retriever = get_reranked_retriever(chroma_collection)
    else:
        from src.kg.retriever import get_kg_retriever

        retriever = get_kg_retriever(
            collection_name=chroma_collection,
            graph_scope=graph_scope or chroma_collection,
        )

    docs = list(retriever.invoke(question))
    return docs, time.perf_counter() - start


def generate_answer(question: str, docs: list[Any]) -> tuple[str, float]:
    """Generate an answer with the same default prompt for every method."""
    from langchain_core.output_parsers import StrOutputParser

    from src.chain.rag_chain import _format_docs
    from src.config import get_settings
    from src.models import get_llm
    from src.prompts import build_tutor_prompt
    from src.prompts.templates import (
        default_tutoring_instructions,
        format_conversation_summary,
        format_course_specific_instructions,
    )

    prompt = build_tutor_prompt(template_variant="default")
    llm = get_llm(get_settings().temperature)
    chain = prompt | llm | StrOutputParser()
    start = time.perf_counter()
    answer = chain.invoke(
        {
            "context": _format_docs(docs),
            "question": question,
            "chat_history": [],
            "tutoring_instructions": default_tutoring_instructions(),
            "course_specific_instructions": format_course_specific_instructions(None),
            "conversation_summary": format_conversation_summary(None),
        }
    )
    return str(answer).strip(), time.perf_counter() - start


def docs_to_review_chunks(docs: list[Any]) -> list[ReviewChunk]:
    """Convert LangChain documents into serializable review chunks."""
    chunks: list[ReviewChunk] = []
    for index, doc in enumerate(docs, start=1):
        metadata = dict(getattr(doc, "metadata", {}) or {})
        score, score_type = _extract_score(metadata)
        chunks.append(
            ReviewChunk(
                rank=index,
                chunk_id=str(metadata.get("chunk_id") or ""),
                document_id=str(metadata.get("document_id") or metadata.get("source_file") or ""),
                source=str(metadata.get("source_file") or metadata.get("source") or "unknown"),
                page=str(metadata.get("page") or ""),
                text=str(getattr(doc, "page_content", "")),
                score=score,
                score_type=score_type,
            )
        )
    return chunks


def _extract_score(metadata: dict[str, Any]) -> tuple[float | None, str]:
    if "rerank_score" in metadata:
        return float(metadata["rerank_score"]), "rerank_score"
    if "vector_distance" in metadata:
        return float(metadata["vector_distance"]), "vector_distance"
    return None, ""


def build_reviews(
    questions: list[ReviewQuestion],
    *,
    methods: list[MethodName],
    chroma_collection: str,
    graph_scope: str | None,
    seed: int | None,
    final_top_k: int,
    skip_generation: bool,
) -> list[MethodReview]:
    """Build anonymized method reviews for every question."""
    reviews: list[MethodReview] = []
    for question_index, question in enumerate(questions, start=1):
        labels = build_anonymous_labels(methods, seed=seed, query_id=question.query_id)
        print(f"Processing question {question_index}/{len(questions)}...", flush=True)
        for method in methods:
            docs, retrieval_latency = retrieve_documents(
                method=method,
                question=question.question,
                chroma_collection=chroma_collection,
                graph_scope=graph_scope,
            )
            docs = docs[:final_top_k]
            if skip_generation:
                answer = "[Answer generation skipped]"
                generation_latency = None
            else:
                answer, generation_latency = generate_answer(question.question, docs)

            reviews.append(
                MethodReview(
                    query_id=question.query_id,
                    method=method,
                    anonymous_label=labels[method],
                    answer=answer,
                    chunks=docs_to_review_chunks(docs),
                    retrieval_latency_seconds=retrieval_latency,
                    generation_latency_seconds=generation_latency,
                )
            )
    return reviews


def write_review_markdown(
    questions: list[ReviewQuestion],
    reviews: list[MethodReview],
    path: Path,
) -> None:
    """Write a human-readable anonymized Markdown review."""
    path.parent.mkdir(parents=True, exist_ok=True)
    reviews_by_query = _reviews_by_query(reviews)
    question_by_id = {question.query_id: question for question in questions}

    lines = [
        "# Anonymized Retrieval Review",
        "",
        "Method identities are hidden in this document. Use the separate key file after review.",
        "Each method is normalized to the same final chunk count before answer generation.",
        "",
    ]
    for query_id in [question.query_id for question in questions]:
        question = question_by_id[query_id]
        lines.extend([f"## {query_id}", "", f"**Question:** {question.question}", ""])
        for review in sorted(reviews_by_query[query_id], key=lambda item: item.anonymous_label):
            lines.extend(
                [
                    f"### {review.anonymous_label}",
                    "",
                    f"- Retrieval latency: {review.retrieval_latency_seconds:.3f}s",
                    "- Generation latency: "
                    + (
                        f"{review.generation_latency_seconds:.3f}s"
                        if review.generation_latency_seconds is not None
                        else "not generated"
                    ),
                    "",
                    "**Answer:**",
                    "",
                    review.answer.strip(),
                    "",
                    "**Retrieved chunks:**",
                    "",
                ]
            )
            for chunk in review.chunks:
                lines.extend(
                    [
                        f"#### Chunk {chunk.rank}",
                        "",
                        f"- Chunk ID: `{chunk.chunk_id or 'unknown'}`",
                        f"- Source: `{chunk.source}`",
                        f"- Page: `{chunk.page or 'unknown'}`",
                        f"- Score: `{_format_optional_score(chunk.score)} {chunk.score_type}`".strip(),
                        "",
                        "```text",
                        chunk.text.strip(),
                        "```",
                        "",
                    ]
                )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_anonymized_jsonl(
    questions: list[ReviewQuestion],
    reviews: list[MethodReview],
    path: Path,
) -> None:
    """Write anonymized machine-readable review records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    question_by_id = {question.query_id: question for question in questions}
    with path.open("w", encoding="utf-8") as handle:
        for review in reviews:
            question = question_by_id[review.query_id]
            payload = {
                "query_id": review.query_id,
                "question": question.question,
                "method_label": review.anonymous_label,
                "answer": review.answer,
                "retrieval_latency_seconds": review.retrieval_latency_seconds,
                "generation_latency_seconds": review.generation_latency_seconds,
                "chunks": [asdict(chunk) for chunk in review.chunks],
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_answer_key(reviews: list[MethodReview], path: Path) -> None:
    """Write the de-anonymization key."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["query_id", "method_label", "actual_method"],
        )
        writer.writeheader()
        for review in sorted(reviews, key=lambda item: (item.query_id, item.anonymous_label)):
            writer.writerow(
                {
                    "query_id": review.query_id,
                    "method_label": review.anonymous_label,
                    "actual_method": review.method,
                }
            )


def _reviews_by_query(reviews: list[MethodReview]) -> dict[str, list[MethodReview]]:
    grouped: dict[str, list[MethodReview]] = {}
    for review in reviews:
        grouped.setdefault(review.query_id, []).append(review)
    return grouped


def _format_optional_score(score: float | None) -> str:
    if score is None:
        return "n/a"
    return f"{score:.6g}"


def resolve_run_output_dir(base_output_dir: Path, *, run_id: str | None) -> Path:
    """Return a unique output directory for this review run."""
    resolved_run_id = run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    candidate = base_output_dir / resolved_run_id
    if not candidate.exists():
        return candidate

    suffix = 2
    while True:
        suffixed_candidate = base_output_dir / f"{resolved_run_id}_{suffix}"
        if not suffixed_candidate.exists():
            return suffixed_candidate
        suffix += 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate anonymized answer/chunk review material for retrieval methods."
    )
    parser.add_argument("--input", required=True, type=Path, help="JSON or numbered text questions.")
    parser.add_argument(
        "--chroma-collection",
        required=True,
        help="Course Chroma collection/scope, e.g. TEST101_v5.",
    )
    parser.add_argument(
        "--graph-scope",
        default=None,
        help="Neo4j graph scope for KG-RAG. Defaults to --chroma-collection.",
    )
    parser.add_argument(
        "--methods",
        default="vector_rag,reranked_rag,kg_rag",
        help="Comma-separated methods: vector_rag, reranked_rag, kg_rag.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/retrieval_review"),
        help="Base directory where a new per-run output folder will be created.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional output run folder name. Defaults to run_YYYYMMDD_HHMMSS.",
    )
    parser.add_argument(
        "--final-top-k",
        type=int,
        default=5,
        help="Number of retrieved chunks each method may send to answer generation/review.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N questions.",
    )
    parser.add_argument("--seed", type=int, default=123, help="Seed for method anonymization.")
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Only export retrieved chunks; do not call the generator LLM.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.final_top_k <= 0:
        raise SystemExit("--final-top-k must be greater than zero.")
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be greater than zero when provided.")

    questions = parse_questions(args.input)
    if args.limit is not None:
        questions = questions[: args.limit]
    methods = parse_methods(args.methods)
    graph_scope = args.graph_scope or args.chroma_collection
    run_output_dir = resolve_run_output_dir(args.output_dir, run_id=args.run_id)
    reviews = build_reviews(
        questions,
        methods=methods,
        chroma_collection=args.chroma_collection,
        graph_scope=graph_scope,
        seed=args.seed,
        final_top_k=args.final_top_k,
        skip_generation=args.skip_generation,
    )

    review_path = run_output_dir / "review.md"
    jsonl_path = run_output_dir / "review_records.jsonl"
    key_path = run_output_dir / "review_key.csv"
    write_review_markdown(questions, reviews, review_path)
    write_anonymized_jsonl(questions, reviews, jsonl_path)
    write_answer_key(reviews, key_path)

    print(f"Wrote anonymized Markdown review to {review_path}")
    print(f"Wrote anonymized JSONL records to {jsonl_path}")
    print(f"Wrote de-anonymization key to {key_path}")


if __name__ == "__main__":
    main()
