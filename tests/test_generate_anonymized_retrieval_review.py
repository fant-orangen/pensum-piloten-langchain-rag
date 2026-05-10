import csv
import json

from scripts.generate_anonymized_retrieval_review import (
    MethodReview,
    ReviewChunk,
    build_anonymous_labels,
    parse_methods,
    parse_questions,
    resolve_run_output_dir,
    write_anonymized_jsonl,
    write_answer_key,
    write_review_markdown,
)


def test_parse_questions_supports_numbered_text(tmp_path) -> None:
    path = tmp_path / "questions.txt"
    path.write_text("1. What is paging?\n\n2) What is a lock?", encoding="utf-8")

    questions = parse_questions(path)

    assert [question.query_id for question in questions] == ["q1", "q2"]
    assert [question.question for question in questions] == ["What is paging?", "What is a lock?"]


def test_parse_questions_supports_json_input(tmp_path) -> None:
    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps([{"id": "vm-1", "question": "What is virtual memory?"}]),
        encoding="utf-8",
    )

    questions = parse_questions(path)

    assert questions[0].query_id == "vm-1"
    assert questions[0].question == "What is virtual memory?"


def test_build_anonymous_labels_is_stable_per_query() -> None:
    methods = parse_methods("vector_rag,reranked_rag,kg_rag")

    first = build_anonymous_labels(methods, seed=123, query_id="q1")
    second = build_anonymous_labels(methods, seed=123, query_id="q1")

    assert first == second
    assert sorted(first.values()) == ["Method A", "Method B", "Method C"]


def test_outputs_are_anonymized_and_key_contains_mapping(tmp_path) -> None:
    questions_path = tmp_path / "questions.txt"
    questions_path.write_text("1. What is paging?", encoding="utf-8")
    questions = parse_questions(questions_path)
    reviews = [
        MethodReview(
            query_id="q1",
            method="kg_rag",
            anonymous_label="Method A",
            answer="Answer text",
            chunks=[
                ReviewChunk(
                    rank=1,
                    chunk_id="chunk_1",
                    document_id="doc_1",
                    source="source.pdf",
                    page="3",
                    text="Chunk text",
                    score=0.9,
                    score_type="rerank_score",
                )
            ],
            retrieval_latency_seconds=0.1,
            generation_latency_seconds=0.2,
        )
    ]

    review_path = tmp_path / "review.md"
    jsonl_path = tmp_path / "review_records.jsonl"
    key_path = tmp_path / "review_key.csv"
    write_review_markdown(questions, reviews, review_path)
    write_anonymized_jsonl(questions, reviews, jsonl_path)
    write_answer_key(reviews, key_path)

    review_text = review_path.read_text(encoding="utf-8")
    json_record = json.loads(jsonl_path.read_text(encoding="utf-8"))
    with key_path.open(encoding="utf-8") as handle:
        key_row = next(csv.DictReader(handle))

    assert "Method A" in review_text
    assert "kg_rag" not in review_text
    assert json_record["method_label"] == "Method A"
    assert "actual_method" not in json_record
    assert key_row == {
        "query_id": "q1",
        "method_label": "Method A",
        "actual_method": "kg_rag",
    }


def test_resolve_run_output_dir_uses_new_folder_and_avoids_overwrite(tmp_path) -> None:
    first = resolve_run_output_dir(tmp_path, run_id="run_fixed")
    first.mkdir()

    second = resolve_run_output_dir(tmp_path, run_id="run_fixed")

    assert first == tmp_path / "run_fixed"
    assert second == tmp_path / "run_fixed_2"


def test_question_limit_can_be_applied_before_building_reviews(tmp_path) -> None:
    path = tmp_path / "questions.txt"
    path.write_text("1. First?\n\n2. Second?\n\n3. Third?", encoding="utf-8")

    questions = parse_questions(path)[:2]

    assert [question.query_id for question in questions] == ["q1", "q2"]
