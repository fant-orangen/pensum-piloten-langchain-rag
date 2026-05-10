import csv
import json

from scripts.analyze_retrieval_speed import (
    load_latency_records,
    summarize_latency,
    write_json_summary,
    write_markdown_report,
)


def test_load_latency_records_joins_key_by_query_and_label(tmp_path) -> None:
    records_path = tmp_path / "review_records.jsonl"
    key_path = tmp_path / "review_key.csv"
    records_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "query_id": "q1",
                        "method_label": "Method B",
                        "retrieval_latency_seconds": 0.2,
                    }
                ),
                json.dumps(
                    {
                        "query_id": "q2",
                        "method_label": "Method B",
                        "retrieval_latency_seconds": 0.5,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    with key_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["query_id", "method_label", "actual_method"],
        )
        writer.writeheader()
        writer.writerow(
            {"query_id": "q1", "method_label": "Method B", "actual_method": "kg_rag"}
        )
        writer.writerow(
            {
                "query_id": "q2",
                "method_label": "Method B",
                "actual_method": "vector_rag",
            }
        )

    records = load_latency_records(records_path, key_path)

    assert [record.actual_method for record in records] == ["kg_rag", "vector_rag"]
    assert [record.retrieval_latency_seconds for record in records] == [0.2, 0.5]


def test_summarize_latency_computes_basic_statistics() -> None:
    records = [
        _record("vector_rag", 1.0),
        _record("vector_rag", 3.0),
        _record("vector_rag", 5.0),
        _record("kg_rag", 2.0),
    ]

    summaries = summarize_latency(records)

    vector_summary = next(summary for summary in summaries if summary.method == "vector_rag")
    assert vector_summary.count == 3
    assert vector_summary.mean_seconds == 3.0
    assert vector_summary.median_seconds == 3.0
    assert vector_summary.stdev_seconds == 2.0
    assert vector_summary.p95_seconds == 4.8


def test_write_reports(tmp_path) -> None:
    summaries = summarize_latency([_record("vector_rag", 1.0), _record("vector_rag", 2.0)])
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "summary.json"

    write_markdown_report(summaries, [_record("vector_rag", 1.0)], markdown_path)
    write_json_summary(summaries, json_path)

    assert "Retrieval Speed Analysis" in markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload[0]["method"] == "vector_rag"


def _record(method: str, latency: float):
    from scripts.analyze_retrieval_speed import LatencyRecord

    return LatencyRecord(
        query_id="q1",
        method_label="Method A",
        actual_method=method,
        retrieval_latency_seconds=latency,
    )
