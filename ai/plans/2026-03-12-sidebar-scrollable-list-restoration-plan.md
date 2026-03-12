# Restore a Proper Scrollable Conversation List

## Summary
- The current sidebar is no longer behaving like a vertical list because the CSS now reaches too far into Gradio's internal radio markup. That likely turned the selector internals into a broken multi-column/grid-like layout instead of a normal stacked list.
- The fix should keep `conversation_selector` as a `gr.Radio`, preserve all existing event wiring, and move scrolling and sizing responsibility back to an outer sidebar container.
- No backend or state changes are needed. This is a frontend layout/CSS correction.

## Commit Plan
1. `docs(plan): add sidebar scrollable list restoration plan`
- Save this plan under `ai/plans` with today's date.
- Record the chosen defaults:
  - keep `gr.Radio`
  - restore a single-column vertical list
  - make the outer sidebar list area the only scroll surface
  - keep the conversation count below the scrollable list

2. `refactor(chat-ui): decouple sidebar sizing from gradio radio internals`
- Update `src/ui/pages/chat_page.py` so the sidebar keeps explicit outer hooks for the conversations block and scroll container, but stops relying on internal `.wrap` / `fieldset` layout overrides for height management.
- Keep the existing selector hook (`chat-conversation-selector`) because the event wiring already depends on the component, but treat it as content inside the scroll shell rather than the scroll shell itself.

3. `fix(chat-ui): restore the conversation selector to a vertical list`
- Remove or replace the selector-specific CSS that forces Gradio radio internals into custom flex-height behavior.
- Keep the label suppression so `Radio` stays hidden.
- Ensure each conversation option renders as one full-width row in a single column, with no clipped duplicate column or grid-like spillover.

4. `feat(chat-ui): make the sidebar list container the only scrollable surface`
- Put `overflow-y: auto` on the dedicated sidebar list container instead of the fragile inner Gradio wrapper.
- Keep the desktop height aligned with the visible chat transcript area above the composer.
- Preserve the mobile/narrow-screen bounded behavior with a breakpoint-specific max height.
- Avoid nested scroll regions so mouse wheel and trackpad scrolling work consistently.

5. `test(chat-ui): lock single-column list and outer-scroll behavior`
- Update `tests/test_chat_page_ui.py` to assert:
  - the sidebar still exposes the selector and outer list container hooks
  - the CSS hides the generated selector label
  - the scroll rule is attached to the outer sidebar list container, not the inner Gradio `.wrap`
  - the old brittle `.wrap` / `fieldset` layout override is no longer required
  - the narrow-layout bounded rule still exists
- Re-run the existing sidebar-loading and chat UI suites so the restored list layout does not break full conversation loading or selection behavior.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_sidebar_loading_ui.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat/UI suites pass
- Manual UI check:
  - the conversation list is a single vertical list, not a grid
  - the list scrolls inside the sidebar
  - all loaded conversations remain reachable
  - the list still stops above the composer and `Send` button
  - `Radio` remains hidden

## Assumptions
- The current broken layout is caused by over-customizing Gradio's internal radio markup rather than by data loading.
- The correct long-term fix is to keep Gradio's default radio option stacking and style only stable outer containers plus minimal selector-specific label suppression.
- The conversation count should remain visible below the scrollable list instead of scrolling with it.
