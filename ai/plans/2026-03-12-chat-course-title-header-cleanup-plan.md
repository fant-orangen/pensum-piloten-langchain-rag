# Replace the Chat Header Block with the Course Name

## Summary
- Remove the current four-line header block on the chat page:
  - `Chat`
  - `Chat med tutor (RAG).`
  - `Åpen samtale: ...`
  - `Lastet samtale: ...`
- Replace that block with a single course-title header that shows only the course name when available.
- If no course is selected or the title cannot be resolved yet, show `Ingen fag valgt`.

## Important Interface Changes
- Update `ChatPageComponents` so the chat page exposes a dedicated course-title component instead of separate title/subtitle/open-conversation header components.
- Keep the existing chat handler output contract largely intact for message sending/loading, but stop using the old header-only conversation text outputs in the page UI.
- Keep transient status/error feedback available elsewhere in the chat page instead of using the top header block for conversation metadata.

## Commit Plan
1. `docs(plan): add chat course-title header cleanup plan`
- Save this plan under `ai/plans` with today’s date.
- Record the chosen defaults:
  - show only the course name when available
  - show `Ingen fag valgt` when no course can be resolved

2. `refactor(chat-ui): replace legacy chat header fields with course title hook`
- Update `src/ui/pages/chat_page.py` to remove the current title/subtitle/open-conversation header block and introduce one dedicated course-title Markdown component.
- Remove now-obsolete header-specific component fields from `ChatPageComponents`.
- Keep a smaller status surface in the page only for actionable feedback, not conversation metadata.

3. `feat(chat-ui): resolve and render the active course name in chat`
- Add a chat-specific course-title resolver that prefers `state["course_name"]` and falls back to course lookup by `course_id` when needed.
- Use that resolver from `src/ui/main_app.py` when rendering the chat page.
- Make the student chat flow populate `course_name` when a course is selected, and ensure route/bootstrap flows still show the right header after auto-selecting a first enrolled course.

4. `refactor(chat-handlers): stop surfacing conversation metadata in the header area`
- Remove the `Åpen samtale` and `Lastet samtale` strings from chat-page presentation.
- Keep conversation state internally unchanged for sidebar selection, loading, refresh, and message sending.
- Preserve useful status/error messaging, but limit it to actual feedback states rather than always-on metadata text.

5. `test(chat-ui): cover course-title header rendering and fallback resolution`
- Update `tests/test_chat_page_ui.py` to assert the new course-title component/hook and the absence of the old header structure.
- Update bootstrap/scope tests to expect the new header behavior instead of `Åpen samtale: Ingen`.
- Add coverage for:
  - course title from `course_name` already in state
  - fallback course title lookup from `course_id`
  - `Ingen fag valgt` when no course is available

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_entry_bootstrap_ui.py tests/test_chat_scope_ui.py`
- Add or update a targeted unit test for the new chat course-title resolver
- `pytest` after the targeted chat/UI suites pass
- Manual UI check:
  - selected course: header shows only the course name
  - no selected course: header shows `Ingen fag valgt`
  - loading/resetting conversations no longer shows `Åpen samtale` or `Lastet samtale` in the header

## Assumptions and Defaults
- The course title should be plain text only, with no `Fag:` prefix.
- The fallback header text is `Ingen fag valgt`.
- Conversation metadata remains in internal state but is no longer presented in the top header area.
- No API/schema changes are required; this is a UI/state-resolution cleanup.
