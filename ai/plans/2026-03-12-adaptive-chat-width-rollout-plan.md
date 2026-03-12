# Adaptive Chat Width When References Open

## Summary
- Replace the current overlay-style references drawer on desktop with a layout that shares horizontal space with the chat area, so the chat widens when references are closed and narrows when they are open.
- Keep the conversation sidebar unchanged on the left.
- Use a different small-screen behavior than desktop: references should move below the chat on mobile instead of overlaying it.

## Important Interface Changes
- Extend `ChatPageComponents` so the chat page exposes a layout container/state for “references open” rather than only a floating drawer surface.
- Keep the existing reference content contract intact: handlers should still produce `references_panel` HTML and `references_status` text.
- Replace the current “drawer visibility only” UI path with a layout-visibility path that can drive desktop width changes and mobile stacking from the same open/closed state.

## Commit Plan
1. `docs(plan): add adaptive chat width rollout plan`
- Save this plan in `ai/plans` with today’s date.
- Record the chosen defaults: adaptive side-by-side on desktop, references below chat on mobile, current source rendering behavior unchanged.

2. `refactor(chat-ui): introduce adaptive chat/reference layout hooks`
- Update `chat_page.py` to replace the fixed-position reference drawer shell with a layout container that can switch between closed and open states.
- Add stable CSS hooks/classes for:
  - desktop closed state: chat uses full available width
  - desktop open state: chat + references share the main workspace row
  - mobile open state: references render below the chat section
- Keep the existing open/close buttons and reference panel component IDs stable where possible.

3. `feat(chat-ui): wire reference open state to layout resizing`
- Replace the current drawer-specific handlers in `references.py` with layout-state helpers that return:
  - open/closed boolean state
  - `gr.update(...)` values for the references container visibility
  - any class/state toggles needed for the chat workspace width change
- Preserve current behavior semantics:
  - selecting an assistant answer with sources opens references
  - user-message selection and empty-source states close or hide the references region
  - manual open/close buttons still work
  - send/new/load/reset flows close references unless a new assistant-selection event reopens them
- Update `main_app.py` event chaining so the new layout outputs are applied consistently after existing chat handler outputs.

4. `feat(chat-ui): make desktop width adaptive and mobile stack below`
- Implement the actual responsive layout rules in `CHAT_PAGE_CSS`:
  - desktop: references occupy a fixed or bounded width column only when open; chat flexes to fill the remaining width
  - desktop closed: references column collapses out of layout so chat expands
  - mobile/tablet breakpoint: references become a full-width section below chat when open
- Ensure scroll behavior remains sane for both chat and references panes, and avoid double scroll traps.

5. `test(chat-ui): cover adaptive width state transitions`
- Update `test_chat_page_ui.py` to assert the new adaptive layout hooks instead of the fixed drawer shell.
- Update `test_chat_references_ui.py` to cover:
  - manual open/close state helpers
  - assistant selection opens references
  - empty/default/user-selection states collapse references
  - layout update outputs target the adaptive container rather than overlay visibility only
- Re-run the existing chat scope/bootstrap suites to confirm the extra UI outputs do not break route/load/reset behavior.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat suites pass
- Manual UI check:
  - desktop closed: chat expands to fill main area
  - desktop open: chat narrows and references appear beside it
  - mobile open: references appear below chat, not over it

## Assumptions and Defaults
- The left conversation sidebar remains unchanged.
- The adaptive-width behavior is only needed for the chat/references region, not the entire page shell.
- Desktop should use side-by-side layout when references are open; mobile should stack references below chat.
- Reference rendering content and source hydration behavior remain unchanged unless required to support the new open/closed layout state.
