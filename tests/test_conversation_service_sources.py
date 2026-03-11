"""Unit tests for frontend source normalization in conversation service."""

from __future__ import annotations

import src.ui.services.conversation_service as conversation_service


def test_normalize_sources_payload_handles_structured_legacy_and_malformed() -> None:
    payload = [
        {"document": "d1.pdf", "page": 3, "excerpt": "  alpha   beta  "},
        {"source_file": "d2.pdf", "page": "7", "text": "legacy text"},
        "d3.pdf",
        {"bad": "value"},
        123,
    ]

    normalized = conversation_service.normalize_sources_payload(payload)

    assert normalized == [
        {"document": "d1.pdf", "page": "3", "excerpt": "alpha beta"},
        {"document": "d2.pdf", "page": "7", "excerpt": "legacy text"},
        {"document": "d3.pdf", "page": "", "excerpt": ""},
        {"document": "Ukjent dokument", "page": "", "excerpt": ""},
    ]


def test_normalize_sources_payload_cleans_html_entities_tags_and_line_breaks() -> None:
    normalized = conversation_service.normalize_sources_payload(
        [
            {
                "document": "doc.pdf",
                "page": 1,
                "excerpt": "<p>&Aring;pning</p><script>bad()</script><br>linje 2&nbsp;&nbsp;her",
            }
        ]
    )

    assert normalized == [
        {"document": "doc.pdf", "page": "1", "excerpt": "Åpning\nlinje 2 her"}
    ]


def test_normalize_sources_payload_truncates_long_excerpt() -> None:
    long_text = "word " * 100

    normalized = conversation_service.normalize_sources_payload(
        [{"document": "doc.pdf", "page": 1, "excerpt": long_text}]
    )

    assert len(normalized[0]["excerpt"]) == 220
    assert normalized[0]["excerpt"].endswith("...")


def test_get_messages_normalizes_sources(monkeypatch) -> None:
    def _fake_get(path: str, *, token: str | None = None):
        del path, token
        return {
            "items": [
                {
                    "id": "m1",
                    "role": "ai",
                    "content": "A",
                    "sources": [{"filename": "docA.pdf", "content": "chunk text"}],
                },
                {
                    "id": "m2",
                    "role": "human",
                    "content": "B",
                    "sources": None,
                },
            ],
            "total": 2,
        }

    monkeypatch.setattr(conversation_service, "get", _fake_get)

    items, total, err = conversation_service.get_messages("token", "conv-id")

    assert err == ""
    assert total == 2
    assert items[0]["sources"] == [
        {"document": "docA.pdf", "page": "", "excerpt": "chunk text"}
    ]
    assert items[1]["sources"] == []


def test_send_message_normalizes_sources(monkeypatch) -> None:
    def _fake_post(path: str, body=None, *, token: str | None = None):
        del path, body, token
        return {
            "id": "m3",
            "role": "ai",
            "content": "answer",
            "sources": "docB.pdf",
        }

    monkeypatch.setattr(conversation_service, "post", _fake_post)

    ok, err, item = conversation_service.send_message("token", "conv-id", "hello")

    assert ok is True
    assert err == ""
    assert item is not None
    assert item["sources"] == [{"document": "docB.pdf", "page": "", "excerpt": ""}]
