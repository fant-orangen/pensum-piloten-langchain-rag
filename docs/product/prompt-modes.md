# Prompt Modes

Prompt modes are stored as integers.

| Value | Mode | Source enum |
|---:|---|---|
| `1` | Socratic | `SystemPromptMode.SOCRATIC` |
| `2` | Direct | `SystemPromptMode.DIRECT` |
| `3` | Example | `SystemPromptMode.EXAMPLE` |

Source files:

- `src/api/schemas/preferences.py`
- `src/api/services/preferences.py`
- `src/prompts/templates.py`
- `frontend/src/pages/ChatPage.tsx`

## Preference Behavior

Users change prompt mode in the chat page.

Backend behavior:

- `PATCH /preferences/system-prompt` stores the selected mode on `app_user.system_prompt_mode`;
- new conversations copy the user's current mode into `conversation.system_prompt_mode`;
- existing conversations keep their stored mode.

## Mode Behavior

| Mode | Product intent |
|---|---|
| Socratic | Guide the student through focused questions and hints. |
| Direct | Answer the question directly before optional follow-up guidance. |
| Example | Explain with a concrete example before generalising. |

## Course Instructions

Course-specific instructions are appended to tutor prompts when configured.

They are stored on:

```text
course.course_specific_instructions
```

They are used with the selected prompt mode and retrieved course context.
