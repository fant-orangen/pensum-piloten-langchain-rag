# Replace Tutor Mode Radio with a Dropdown and Remove the Helper Text

## Summary
- The tutor mode control in the left sidebar is currently a `gr.Radio` with the info text `Brukes for nye samtaler og blir standard til du endrer den.`
- The handlers already treat the control as a simple selected integer mode, so this can stay a frontend-only control swap: remove the helper text and replace the radio with a dropdown while keeping the same mode values and existing event wiring.
- No backend or chat-state changes are required.

## Commit Plan
1. `docs(plan): add tutor mode dropdown cleanup plan`
- Save this plan under `ai/plans` with today's date.
- Record the chosen defaults:
  - remove the helper/info text entirely
  - replace the tutor mode radio with a dropdown
  - keep the existing mode values and labels unchanged

2. `refactor(chat-ui): switch tutor mode selector from radio to dropdown`
- Update `src/ui/pages/chat_page.py` so `mode_selector` becomes a `gr.Dropdown` instead of `gr.Radio`.
- Keep the component field name `mode_selector` in `ChatPageComponents` so existing event wiring in `src/ui/main_app.py` does not need a wider contract change.
- Remove the `info=` text entirely.
- Keep the visible label `Veiledningsmodus`.
- Keep `_MODE_CHOICES` as the source of truth so the dropdown still maps to the same numeric mode values (`1`, `2`, `3`).

3. `feat(chat-ui): tune dropdown styling for the sidebar`
- Add or adjust CSS in `src/ui/pages/chat_page.py` so the dropdown fits the existing sidebar card styling and width cleanly.
- Ensure the control looks intentional in the narrow sidebar and does not inherit any leftover radio-specific spacing assumptions.

4. `test(chat-ui): cover dropdown mode selector and removed helper text`
- Update `tests/test_chat_page_ui.py` to assert:
  - `mode_selector` is now a dropdown component
  - the selector still exists under the same `ChatPageComponents` field
  - the old helper text is no longer present in the page definition/CSS expectations
  - the page still exposes the same sidebar hooks
- Add or update a handler-oriented test if needed to confirm the selected dropdown value still flows into new-conversation and send handlers unchanged.

## Important Interface Changes
- `ChatPageComponents.mode_selector` changes type from `gr.Radio` to `gr.Dropdown`.
- No change to event inputs/outputs in `src/ui/main_app.py`; it still passes `chat_page.mode_selector` into the existing handlers.
- No change to `_MODE_CHOICES`, `_MODE_LABELS`, or the backend preference update path.

## Test Plan
- `pytest tests/test_chat_page_ui.py`
- Re-run chat flow tests that cover new conversation creation and message sending, especially paths that pass `selected_mode`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat/UI suites pass
- Manual UI check:
  - the helper text is gone
  - the mode control is a dropdown, not a radio group
  - selecting a mode still affects newly created conversations and mode-save behavior exactly as before

## Assumptions
- The dropdown should keep the existing English option labels: `Socratic mode`, `Direct mode`, `Example mode`.
- The visible field label remains `Veiledningsmodus`.
- The selected value should remain the same numeric mode ID so no handler or API behavior changes are needed.
