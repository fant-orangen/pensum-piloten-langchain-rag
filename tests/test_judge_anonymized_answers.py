import csv
import json

from scripts.judge_anonymized_answers import (
    AnswerJudgment,
    JudgmentRecord,
    ReviewAnswer,
    format_chunks_for_prompt,
    load_review_answers,
    parse_judgment_response,
    resolve_paths,
    summarize_by_method,
    write_judgments_jsonl,
    write_report,
    write_summary_csv,
)


def test_parse_judgment_response_accepts_fenced_json() -> None:
    judgment = parse_judgment_response(
        """```json
        {
          "correctness": 5,
          "relevance": 4,
          "clarity": 3,
          "pedagogical_usefulness": 4,
          "faithfulness_to_chunks": 5,
          "overall": 4,
          "short_explanation": "Good answer."
        }
        ```"""
    )

    assert judgment.correctness == 5
    assert judgment.short_explanation == "Good answer."


def test_format_chunks_for_prompt_truncates_long_chunks() -> None:
    formatted = format_chunks_for_prompt(
        [{"chunk_id": "c1", "source": "doc.pdf", "page": "1", "text": "abcdef"}],
        max_chunk_chars=3,
    )

    assert "abc\n[truncated]" in formatted


def test_load_review_answers_respects_limit(tmp_path) -> None:
    path = tmp_path / "review_records.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(_review_payload("q1")),
                json.dumps(_review_payload("q2")),
            ]
        ),
        encoding="utf-8",
    )

    answers = load_review_answers(path, limit=1)

    assert answers == [
        ReviewAnswer(
            query_id="q1",
            question="Question q1?",
            method_label="Method A",
            answer="Answer q1",
            chunks=[],
        )
    ]


def test_resolve_paths_from_run_dir(tmp_path) -> None:
    run_dir = tmp_path / "run"

    paths = resolve_paths(
        run_dir=run_dir,
        records=None,
        key=None,
        judgments_output=None,
        summary_output=None,
        report_output=None,
    )

    assert paths == (
        run_dir / "review_records.jsonl",
        run_dir / "review_key.csv",
        run_dir / "answer_judgments.jsonl",
        run_dir / "answer_judgment_summary.csv",
        run_dir / "answer_judgment_report.md",
    )


def test_summary_and_outputs_are_blinded_until_summary_join(tmp_path) -> None:
    judgments = [
        JudgmentRecord(
            query_id="q1",
            question="Question?",
            method_label="Method A",
            judge_model="test-model",
            judgment=AnswerJudgment(
                correctness=5,
                relevance=4,
                clarity=4,
                pedagogical_usefulness=3,
                faithfulness_to_chunks=5,
                overall=4,
                short_explanation="Solid.",
            ),
        )
    ]
    key = {("q1", "Method A"): "kg_rag"}

    summaries = summarize_by_method(judgments, key)
    judgments_path = tmp_path / "answer_judgments.jsonl"
    summary_path = tmp_path / "summary.csv"
    report_path = tmp_path / "report.md"
    write_judgments_jsonl(judgments, judgments_path)
    write_summary_csv(summaries, summary_path)
    write_report(summaries, judgments, report_path)

    raw_judgment = json.loads(judgments_path.read_text(encoding="utf-8"))
    with summary_path.open(encoding="utf-8") as handle:
        summary_row = next(csv.DictReader(handle))

    assert raw_judgment["method_label"] == "Method A"
    assert "actual_method" not in raw_judgment
    assert summary_row["method"] == "kg_rag"
    assert "kg_rag" in report_path.read_text(encoding="utf-8")


def _review_payload(query_id: str) -> dict[str, object]:
    return {
        "query_id": query_id,
        "question": f"Question {query_id}?",
        "method_label": "Method A",
        "answer": f"Answer {query_id}",
        "chunks": [],
    }
