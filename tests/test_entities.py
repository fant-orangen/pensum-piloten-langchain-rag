from src.ingestion.entities import clean_entities, extract_entities


def test_clean_entities_removes_stopword_phrases() -> None:
    entities = clean_entities(["memory the", "the memory", "physical memory", "memory"])
    assert "memory the" not in entities
    assert "the memory" not in entities
    assert "physical memory" in entities
    assert "memory" in entities


def test_extract_entities_filters_query_fillers() -> None:
    extracted = extract_entities("Can you help me understand memory addresses?")
    assert "memory" in extracted
    assert "addresses" in extracted or "address" in extracted
    assert "can" not in extracted
    assert "help" not in extracted
    assert "understand" not in extracted


def test_extract_entities_spacy_fallback_to_rule() -> None:
    extracted = extract_entities(
        "Virtual memory uses address translation.",
        extractor="spacy",
        spacy_model_name="nonexistent_spacy_model_for_test",
    )
    assert "memory" in extracted
