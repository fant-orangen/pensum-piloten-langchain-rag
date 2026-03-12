# Hide the Open Button While References Are Open

## Summary
- The current chat page uses one toolbar button to open references and a separate in-panel `Lukk` button to close them, but the open button stays visible after the panel opens, which makes the control feel redundant and confusing.
- This can be fixed entirely in the frontend by treating the toolbar button and in-panel close button as two views of the same open/closed state.
- The chosen behavior is: when references are closed, show the top-right `Kildereferanser` button; when references are open, hide that button and keep only the in-panel `Lukk` control.

## Important Interface Changes
- Extend `ChatPageComponents` so the top-right open-button container can be updated independently from the references panel container.
- Keep the existing reference content contract unchanged: handlers still return `references_panel` HTML and `references_status` text.
- Reuse the existing reference-open boolean state; no new source or conversation state is needed.

## Commit Plan
1. `docs(plan): add reference button visibility cleanup plan`
- Save this plan in `ai/plans` with today’s date.
- Record the chosen default: hide the top-right `Kildereferanser` button whenever references are open.

2. `refactor(chat-ui): add explicit toolbar control hooks for reference button visibility`
- Update `chat_page.py` so the top-right open button sits inside its own addressable container/group instead of being the only thing in an anonymous toolbar column.
- Keep the current button IDs stable if possible, but add a stable hook for the wrapper/container because that is what will be shown/hidden.
- Keep the references panel structure unchanged.

3. `feat(chat-ui): tie toolbar button visibility to reference open state`
- Update the reference layout helpers in `references.py` so the shared open/closed state returns:
  - references container visibility
  - open-button container visibility
- Preserve current behavior semantics:
  - manual open hides the toolbar button and shows the references panel
  - manual close shows the toolbar button and hides the references panel
  - selecting an assistant answer with sources opens the references panel and hides the toolbar button
  - empty/default/user-message states collapse the references panel and restore the toolbar button
  - send/new/load/reset flows still close references and restore the open button

4. `refactor(chat-ui): update event wiring to apply both visibility targets`
- Update `main_app.py` so all existing open/close/layout update chains now output to both:
  - the references container
  - the toolbar open-button container
- Keep the current handler sequencing intact so the visibility update still runs after reference content/status updates.

5. `test(chat-ui): cover open-button visibility transitions`
- Update `test_chat_page_ui.py` to assert the new toolbar control hook.
- Update `test_chat_references_ui.py` so the layout-state helpers assert both visibility outputs:
  - references open => panel visible, toolbar open button hidden
  - references closed => panel hidden, toolbar open button visible
- Re-run the existing chat scope/bootstrap suites to confirm no regressions in the current reference open/close behavior.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat suites pass
- Manual UI check:
  - closed state: top-right `Kildereferanser` button visible
  - open state: top-right button hidden, in-panel `Lukk` visible
  - closing references restores the top-right button

## Assumptions and Defaults
- The top-right button should disappear entirely while references are open, not stay disabled.
- The in-panel `Lukk` button remains the only visible close control once references are open.
- No layout-width, source rendering, or source hydration behavior needs to change for this cleanup.
