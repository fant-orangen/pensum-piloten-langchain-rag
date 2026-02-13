"""Deterministic lightweight entity / term extraction for chunk metadata."""

from __future__ import annotations

import re
from collections import Counter

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")

_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "among",
    "another",
    "because",
    "before",
    "being",
    "between",
    "could",
    "different",
    "does",
    "each",
    "every",
    "from",
    "have",
    "into",
    "just",
    "many",
    "more",
    "most",
    "other",
    "over",
    "same",
    "some",
    "such",
    "than",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "under",
    "very",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
    "into",
    "onto",
    "across",
    "into",
    "within",
    "without",
    "were",
    "been",
    "will",
    "shall",
    "must",
    "should",
    "might",
    "using",
    "used",
    "use",
    "each",
    "text",
    "chapter",
    "section",
    "figure",
    "table",
}

_DOMAIN_TERMS = {
    "algorithm",
    "algorithms",
    "api",
    "cache",
    "concurrency",
    "cpu",
    "database",
    "deadlock",
    "graph",
    "kernel",
    "latency",
    "memory",
    "model",
    "network",
    "operating",
    "process",
    "prompt",
    "query",
    "rag",
    "retrieval",
    "scheduler",
    "semaphore",
    "thread",
    "throughput",
    "vector",
}


def _normalise(token: str) -> str:
    return token.strip("-_").lower()


def extract_entities(text: str, *, max_entities: int = 40) -> list[str]:
    """Extract robust lexical entities/terms from text.

    The method is intentionally simple and deterministic:
    - unigram terms from tokens (alpha-leading, len >= 3)
    - optional bigrams from adjacent content words
    - small boosts for TitleCase and known domain terms
    """
    if not text:
        return []

    raw_tokens = _TOKEN_RE.findall(text)
    if not raw_tokens:
        return []

    unigrams: Counter[str] = Counter()
    titlecase_hits: Counter[str] = Counter()
    sequence: list[str] = []

    for raw in raw_tokens:
        term = _normalise(raw)
        if len(term) < 3 or term in _STOPWORDS or term.isdigit():
            continue
        unigrams[term] += 1
        sequence.append(term)
        if raw[:1].isupper():
            titlecase_hits[term] += 1

    if not unigrams:
        return []

    scores: dict[str, float] = {}
    for term, count in unigrams.items():
        score = float(count)
        if titlecase_hits[term] > 0:
            score += 0.75
        if term in _DOMAIN_TERMS:
            score += 0.5
        scores[term] = score

    bigrams: Counter[str] = Counter()
    for left, right in zip(sequence, sequence[1:]):
        if left in _STOPWORDS or right in _STOPWORDS:
            continue
        bigram = f"{left} {right}"
        bigrams[bigram] += 1

    for term, count in bigrams.items():
        if count < 2:
            continue
        scores[term] = float(count) + 0.3

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [term for term, _ in ranked[:max_entities]]
