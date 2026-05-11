import csv
import json
from pathlib import Path

from scripts.generate_retrieval_evaluation_report import (
    AnswerJudgmentRecord,
    bootstrap_mean_ci,
    compute_overlap_matrix,
    compute_topic_answer_summary,
    compute_winner_counts,
    generate_report,
    jaccard,
    load_answer_judgments,
    load_review_key,
    load_review_records,
)


def test_bootstrap_ci_contains_mean() -> None:
    values = [1, 2, 3, 4, 5]
    low, high = bootstrap_mean_ci(values, samples=200, seed=123)

    assert low <= 3.0 <= high


def test_winner_counts_use_highest_per_query_overall() -> None:
    records = [
        _answer("q1", "kg_rag", overall=5),
        _answer("q1", "vector_rag", overall=4),
        _answer("q2", "kg_rag", overall=3),
        _answer("q2", "vector_rag", overall=3),
    ]

    assert compute_winner_counts(records) == {"kg_rag": 1, "tie": 1}


def test_overlap_matrix_averages_query_jaccard(tmp_path) -> None:
    run_dir = _write_minimal_run(tmp_path)
    key = load_review_key(run_dir / "review_key.csv")
    review_records = load_review_records(run_dir / "review_records.jsonl", key)

    matrix = compute_overlap_matrix(review_records)

    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3
    assert matrix[("kg_rag", "vector_rag")] == 1 / 3


def test_topic_summary_uses_optional_query_metadata() -> None:
    records = [
        _answer("q1", "kg_rag", overall=5),
        _answer("q2", "kg_rag", overall=3),
        _answer("q1", "vector_rag", overall=4),
    ]

    summary = compute_topic_answer_summary(records, {"q1": "locks", "q2": "memory"})

    assert summary[("locks", "kg_rag")] == (1, 5)
    assert summary[("memory", "kg_rag")] == (1, 3)


def test_generate_report_writes_metrics_and_figures(tmp_path) -> None:
    run_dir = _write_minimal_run(tmp_path)
    queries_path = run_dir / "queries.json"
    queries_path.write_text(
        json.dumps([{"id": "q1", "question": "Question?", "metadata": {"topic": "locks"}}]),
        encoding="utf-8",
    )

    generate_report(
        records_path=run_dir / "review_records.jsonl",
        key_path=run_dir / "review_key.csv",
        answer_judgments_path=run_dir / "answer_judgments.jsonl",
        chunk_judgments_path=run_dir / "chunk_judgments.jsonl",
        speed_summary_path=run_dir / "retrieval_speed_summary.json",
        queries_json_path=queries_path,
        output_path=run_dir / "evaluation_report.md",
        metrics_json_path=run_dir / "metrics_summary.json",
        metrics_csv_path=run_dir / "metrics_summary.csv",
        figures_dir=run_dir / "figures",
        bootstrap_samples=50,
        seed=123,
    )

    report = (run_dir / "evaluation_report.md").read_text(encoding="utf-8")
    metrics = json.loads((run_dir / "metrics_summary.json").read_text(encoding="utf-8"))
    with (run_dir / "metrics_summary.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert "Answer Judgment Summary" in report
    assert metrics["winner_counts"] == {"kg_rag": 1}
    assert rows[0]["method"] == "kg_rag"
    assert "<svg" in (run_dir / "figures" / "answer_overall_scores.svg").read_text(
        encoding="utf-8"
    )


def test_load_answer_judgments_joins_with_key(tmp_path) -> None:
    run_dir = _write_minimal_run(tmp_path)
    key = load_review_key(run_dir / "review_key.csv")

    records = load_answer_judgments(run_dir / "answer_judgments.jsonl", key)

    assert records[0].method == "kg_rag"
    assert records[0].scores["overall"] == 5


def _answer(query_id: str, method: str, *, overall: int) -> AnswerJudgmentRecord:
    return AnswerJudgmentRecord(
        query_id=query_id,
        method_label=method,
        method=method,
        scores={
            "correctness": overall,
            "relevance": overall,
            "clarity": overall,
            "pedagogical_usefulness": overall,
            "faithfulness_to_chunks": overall,
            "overall": overall,
        },
    )


def _write_minimal_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "review_key.csv").write_text(
        "query_id,method_label,actual_method\n"
        "q1,Method A,kg_rag\n"
        "q1,Method B,vector_rag\n",
        encoding="utf-8",
    )
    (run_dir / "review_records.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "query_id": "q1",
                        "question": "Question?",
                        "method_label": "Method A",
                        "answer": "Answer A",
                        "retrieval_latency_seconds": 0.2,
                        "generation_latency_seconds": 1.0,
                        "chunks": [
                            {"chunk_id": "a", "document_id": "doc1"},
                            {"chunk_id": "b", "document_id": "doc2"},
                        ],
                    }
                ),
                json.dumps(
                    {
                        "query_id": "q1",
                        "question": "Question?",
                        "method_label": "Method B",
                        "answer": "Answer B",
                        "retrieval_latency_seconds": 0.1,
                        "generation_latency_seconds": 1.0,
                        "chunks": [
                            {"chunk_id": "b", "document_id": "doc2"},
                            {"chunk_id": "c", "document_id": "doc3"},
                        ],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "answer_judgments.jsonl").write_text(
        json.dumps(
            {
                "query_id": "q1",
                "question": "Question?",
                "method_label": "Method A",
                "judgment": {
                    "correctness": 5,
                    "relevance": 5,
                    "clarity": 5,
                    "pedagogical_usefulness": 5,
                    "faithfulness_to_chunks": 5,
                    "overall": 5,
                    "short_explanation": "Strong.",
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "query_id": "q1",
                "question": "Question?",
                "method_label": "Method B",
                "judgment": {
                    "correctness": 3,
                    "relevance": 3,
                    "clarity": 3,
                    "pedagogical_usefulness": 3,
                    "faithfulness_to_chunks": 3,
                    "overall": 3,
                    "short_explanation": "Weaker.",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "chunk_judgments.jsonl").write_text(
        json.dumps(
            {
                "query_id": "q1",
                "method_label": "Method A",
                "judgment": {
                    "label": "direct_relevance",
                    "usefulness_score": 3,
                    "include_in_final_prompt": True,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "retrieval_speed_summary.json").write_text(
        json.dumps(
            [
                {
                    "method": "kg_rag",
                    "count": 1,
                    "mean_seconds": 0.2,
                    "median_seconds": 0.2,
                    "p95_seconds": 0.2,
                    "max_seconds": 0.2,
                }
            ]
        ),
        encoding="utf-8",
    )
    return run_dir
