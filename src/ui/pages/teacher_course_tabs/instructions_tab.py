"""Teacher course instructions tab UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.state import COURSE_ID_KEY, auth_token

MAX_COURSE_INSTRUCTIONS_CHARS = 3000


@dataclass(slots=True)
class TeacherCourseInstructionsTabComponents:
    group: gr.Group
    course_instructions_input: gr.Textbox
    course_instructions_counter: gr.Markdown
    save_course_instructions_button: gr.Button


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def _course_instructions_counter_text(instructions_text: str | None) -> str:
    instruction_length = len(str(instructions_text or ""))
    return f"Tegn brukt: {instruction_length}/{MAX_COURSE_INSTRUCTIONS_CHARS}"


def build_teacher_course_instructions_tab() -> TeacherCourseInstructionsTabComponents:
    with gr.Group() as group:
        gr.Markdown(
            "Legg til egne instruksjoner som blir lagt til systemprompten for dette faget. "
            "Det er foreløpig ikke mulig å hente eksisterende lagrede instruksjoner."
        )
        course_instructions_input = gr.Textbox(
            label="Instruksjoner (maks 3000 tegn)",
            placeholder=(
                "Eksempel: Prioriter pensumbegreper fra uke 1–5, bruk norske fagtermer, "
                "og gi korte stegvise hint før fasitsvar."
            ),
            lines=8,
            max_lines=12,
        )
        course_instructions_counter = gr.Markdown(_course_instructions_counter_text(""))
        save_course_instructions_button = gr.Button(
            "Lagre instruksjoner",
            variant="primary",
        )

    return TeacherCourseInstructionsTabComponents(
        group=group,
        course_instructions_input=course_instructions_input,
        course_instructions_counter=course_instructions_counter,
        save_course_instructions_button=save_course_instructions_button,
    )


def teacher_course_instructions_input_update(_state: dict[str, Any]) -> Any:
    return gr.update(value="")


def teacher_course_instructions_counter_update(_state: dict[str, Any]) -> str:
    return _course_instructions_counter_text("")


def handle_course_instructions_input(instructions_text: str | None) -> str:
    return _course_instructions_counter_text(instructions_text)


def handle_save_course_instructions(
    state: dict[str, Any],
    instructions_text: str | None,
) -> tuple[Any, str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        counter_text = _course_instructions_counter_text(instructions_text)
        return gr.update(value=instructions_text or ""), counter_text, "Fant ikke faget."

    token = auth_token(state)
    if not token:
        counter_text = _course_instructions_counter_text(instructions_text)
        return (
            gr.update(value=instructions_text or ""),
            counter_text,
            "Sessionen er utløpt — logg inn på nytt.",
        )

    raw_instructions = str(instructions_text or "")
    if len(raw_instructions) > MAX_COURSE_INSTRUCTIONS_CHARS:
        counter_text = _course_instructions_counter_text(raw_instructions)
        return (
            gr.update(value=raw_instructions),
            counter_text,
            f"Instruksjonene er for lange. Maks {MAX_COURSE_INSTRUCTIONS_CHARS} tegn.",
        )

    cleaned_instructions = raw_instructions.strip()
    payload_instructions = cleaned_instructions or None

    success, message, _course = _course_api.update_course_instructions(
        token,
        course_id,
        payload_instructions,
    )
    next_input_value = cleaned_instructions if success else raw_instructions
    return (
        gr.update(value=next_input_value),
        _course_instructions_counter_text(next_input_value),
        message,
    )
