import csv
import json

from scripts.judge_retrieved_chunks import (
    ChunkJudgment,
    ChunkJudgmentRecord,
    format_chunk_for_prompt,
    parse_chunk_judgment_response,
    resolve_paths,
    summarize_by_method,
    write_chunk_judgments_jsonl,
    write_report,
    write_summary_csv,
)


def test_parse_chunk_judgment_response_accepts_fenced_json() -> None:
    judgment = parse_chunk_judgment_response(
        """```json
        {
          "label": "direct_relevance",
          "usefulness_score": 3,
          "include_in_final_prompt": true,
          "short_explanation": "Directly explains the concept."
        }
        ```"""
    )

    assert judgment.label == "direct_relevance"
    assert judgment.usefulness_score == 3
    assert judgment.include_in_final_prompt is True


def test_format_chunks_for_prompt_truncates() -> None:
    formatted = format_chunk_for_prompt(
        {"chunk_id": "c1", "source": "doc.pdf", "page": "2", "text": "abcdef"},
        max_chunk_chars=3,
    )

    assert "abc\n[truncated]" in formatted


def test_resolve_paths_from_run_dir(tmp_path) -> None:
    run_dir = tmp_path / "run"

    assert resolve_paths(
        run_dir=run_dir,
        records=None,
        key=None,
        judgments_output=None,
        summary_output=None,
        report_output=None,
    ) == (
        run_dir / "review_records.jsonl",
        run_dir / "review_key.csv",
        run_dir / "chunk_judgments.jsonl",
        run_dir / "chunk_judgment_summary.csv",
        run_dir / "chunk_judgment_report.md",
    )


def test_summary_and_outputs_are_blinded_until_summary_join(tmp_path) -> None:
    judgments = [
        ChunkJudgmentRecord(
            query_id="q1",
            question="Question?",
            method_label="Method A",
            chunk_rank=1,
            chunk_id="c1",
            source="doc.pdf",
            page="2",
            judge_model="test-model",
            judgment=ChunkJudgment(
                label="support_relevance",
                usefulness_score=2,
                include_in_final_prompt=True,
                short_explanation="Useful context.",
            ),
        )
    ]
    key = {("q1", "Method A"): "kg_rag"}

    summaries = summarize_by_method(judgments, key)
    judgments_path = tmp_path / "chunk_judgments.jsonl"
    summary_path = tmp_path / "summary.csv"
    report_path = tmp_path / "report.md"
    write_chunk_judgments_jsonl(judgments, judgments_path)
    write_summary_csv(summaries, summary_path)
    write_report(summaries, judgments, report_path)

    raw_judgment = json.loads(judgments_path.read_text(encoding="utf-8"))
    with summary_path.open(encoding="utf-8") as handle:
        summary_row = next(csv.DictReader(handle))

    assert raw_judgment["method_label"] == "Method A"
    assert "actual_method" not in raw_judgment
    assert summary_row["method"] == "kg_rag"
    assert summary_row["support_relevance"] == "1"
    assert "kg_rag" in report_path.read_text(encoding="utf-8")
