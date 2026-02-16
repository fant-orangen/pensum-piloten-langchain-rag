from src.prompts import build_tutor_prompt, normalise_teaching_mode


def test_normalise_teaching_mode_aliases() -> None:
    assert normalise_teaching_mode("1") == "socratic"
    assert normalise_teaching_mode("2") == "structured_instructor"
    assert normalise_teaching_mode("3") == "active_recall"
    assert normalise_teaching_mode("structured") == "structured_instructor"
    assert normalise_teaching_mode("recall") == "active_recall"


def test_build_tutor_prompt_structured_mode() -> None:
    prompt = build_tutor_prompt("structured_instructor")
    system_text = prompt.messages[0].prompt.template
    assert "expert academic instructor" in system_text.lower()


def test_build_tutor_prompt_active_recall_mode() -> None:
    prompt = build_tutor_prompt("active_recall")
    system_text = prompt.messages[0].prompt.template
    assert "retrieval practice and active recall" in system_text.lower()
