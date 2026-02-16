"""Deterministic lightweight entity / term extraction for chunk metadata."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from typing import Any, cast

import structlog

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")
_ENTITY_TOKEN_RE = re.compile(r"^[a-z][a-z0-9-]{2,}$")

logger = structlog.get_logger(__name__)

_SPACY_MODELS: dict[str, Any] = {}
_SPACY_IMPORT_WARNED = False
_SPACY_MODEL_WARNED: set[str] = set()

STOPWORDS = {
    "a",
    "about",
    "across",
    "after",
    "again",
    "all",
    "also",
    "among",
    "an",
    "and",
    "another",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "between",
    "by",
    "can",
    "cannot",
    "chapter",
    "conclusion",
    "construct",
    "could",
    "did",
    "different",
    "do",
    "does",
    "doing",
    "done",
    "each",
    "every",
    "example",
    "examples",
    "exercise",
    "exercises",
    "figure",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "help",
    "her",
    "his",
    "how",
    "i",
    "if",
    "in",
    "introduction",
    "into",
    "is",
    "it",
    "its",
    "just",
    "know",
    "learned",
    "many",
    "me",
    "might",
    "more",
    "most",
    "must",
    "need",
    "not",
    "of",
    "on",
    "onto",
    "or",
    "other",
    "our",
    "out",
    "over",
    "question",
    "questions",
    "really",
    "reliable",
    "same",
    "section",
    "shall",
    "she",
    "should",
    "some",
    "student",
    "students",
    "such",
    "summary",
    "table",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "under",
    "understand",
    "use",
    "used",
    "using",
    "very",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "within",
    "without",
    "with",
    "would",
    "you",
    "your",
    "text",
}

DOMAIN_TERMS = {
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


def _is_valid_entity_token(token: str) -> bool:
    if not _ENTITY_TOKEN_RE.match(token):
        return False
    return token not in STOPWORDS


def clean_entities(entities: Iterable[str], *, max_entities: int | None = None) -> list[str]:
    """Normalize/filter entity strings and dedupe while preserving order."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for raw in entities:
        if not isinstance(raw, str):
            continue
        entity = raw.strip().lower()
        if not entity:
            continue

        tokens = entity.split()
        if not tokens or len(tokens) > 3:
            continue
        if len(tokens) > 1 and any(token in STOPWORDS for token in tokens):
            continue
        if not all(_is_valid_entity_token(token) for token in tokens):
            continue

        normalized = " ".join(tokens)
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)

        if max_entities is not None and len(cleaned) >= max_entities:
            break

    return cleaned


def _extract_entities_rule(text: str, *, max_entities: int) -> list[str]:
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
        if len(term) < 3 or term in STOPWORDS or term.isdigit():
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
        if term in DOMAIN_TERMS:
            score += 0.5
        scores[term] = score

    bigrams: Counter[str] = Counter()
    for left, right in zip(sequence, sequence[1:]):
        if left in STOPWORDS or right in STOPWORDS:
            continue
        bigram = f"{left} {right}"
        bigrams[bigram] += 1

    for term, count in bigrams.items():
        if count < 2:
            continue
        scores[term] = float(count) + 0.3

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ranked_terms = [term for term, _ in ranked]
    return clean_entities(ranked_terms, max_entities=max_entities)


def _load_spacy_model(model_name: str) -> Any | None:
    global _SPACY_IMPORT_WARNED
    if model_name in _SPACY_MODELS:
        return _SPACY_MODELS[model_name]

    try:
        import spacy  # type: ignore[import-not-found]
    except Exception as exc:  # optional dependency
        if not _SPACY_IMPORT_WARNED:
            logger.warning(
                "spacy_extractor_unavailable",
                reason=str(exc),
                fallback="rule",
            )
            _SPACY_IMPORT_WARNED = True
        return None

    try:
        nlp = spacy.load(model_name)
    except Exception as exc:  # model missing or load failure
        if model_name not in _SPACY_MODEL_WARNED:
            logger.warning(
                "spacy_model_load_failed",
                model_name=model_name,
                reason=str(exc),
                fallback="rule",
            )
            _SPACY_MODEL_WARNED.add(model_name)
        return None

    _SPACY_MODELS[model_name] = nlp
    return nlp


def _extract_entities_spacy(
    text: str,
    *,
    max_entities: int,
    model_name: str,
) -> list[str]:
    if not text:
        return []

    nlp = _load_spacy_model(model_name)
    if nlp is None:
        return []

    doc = nlp(text)
    candidates: list[str] = []

    for ent in cast(Iterable[Any], getattr(doc, "ents", [])):
        label = str(getattr(ent, "label_", ""))
        if label in {"CARDINAL", "DATE", "MONEY", "PERCENT", "TIME"}:
            continue
        candidates.append(str(ent.text))

    for chunk in cast(Iterable[Any], getattr(doc, "noun_chunks", [])):
        candidates.append(str(chunk.text))

    return clean_entities(candidates, max_entities=max_entities)


def _resolve_extractor(
    extractor: str | None,
    spacy_model_name: str | None,
) -> tuple[str, str]:
    from src.config import get_settings

    settings = get_settings()
    resolved_extractor = (extractor or settings.graph_entity_extractor).strip().lower()
    if resolved_extractor not in {"rule", "spacy"}:
        logger.warning(
            "unknown_entity_extractor",
            configured=resolved_extractor,
            fallback="rule",
        )
        resolved_extractor = "rule"
    resolved_model = spacy_model_name or settings.graph_spacy_model_name
    return resolved_extractor, resolved_model


def extract_entities(
    text: str,
    *,
    max_entities: int = 40,
    extractor: str | None = None,
    spacy_model_name: str | None = None,
) -> list[str]:
    resolved_extractor, resolved_model = _resolve_extractor(extractor, spacy_model_name)
    if resolved_extractor == "spacy":
        entities = _extract_entities_spacy(
            text,
            max_entities=max_entities,
            model_name=resolved_model,
        )
        if entities:
            return entities
    return _extract_entities_rule(text, max_entities=max_entities)
