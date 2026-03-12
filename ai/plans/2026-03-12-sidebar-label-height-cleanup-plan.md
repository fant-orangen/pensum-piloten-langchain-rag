# Clean Up Sidebar Header and Constrain Conversation List Height

## Summary
- The sidebar conversation area still has two UI issues after the scrolling work:
  - the `gr.Radio` selector is rendering the text `Radio` above the list
  - the scrollable list is still sized against too much vertical space, so it reaches down toward the composer and `Send` button instead of stopping with the main chat transcript area
- This should remain a frontend-only fix in the chat page layout/CSS layer. No backend or handler-contract changes are needed.

## Important Interface Changes
- Keep `conversation_selector` as a `gr.Radio`, but hide its generated label/legend so `Radio` is no longer visible.
- Keep the sidebar list scrollable, but cap its desktop height to the visible chat content area rather than the full main column height that includes the composer/actions.
- Preserve all current `.change()` wiring and conversation-loading behavior in `src/ui/main_app.py`.

## Commit Plan
1. `docs(plan): add sidebar label and height cleanup plan`
- Save this plan under `ai/plans` with today’s date.
- Record the chosen defaults:
  - hide the generated `Radio` label entirely
  - desktop sidebar list should align with the chat transcript region, not the message composer/buttons
  - narrow layouts keep the bounded internal scroll behavior

2. `refactor(chat-ui): add explicit sidebar transcript-height hooks`
- Update `src/ui/pages/chat_page.py` to add stable hooks for the sidebar controls block and the sidebar conversations block, so the list height can be tied to the right part of the layout.
- Keep the existing selector/list container hooks intact.

3. `feat(chat-ui): remove the generated radio label from the conversation list`
- Configure the conversation selector so Gradio does not render `Radio` above the list.
- If Gradio still emits a wrapper/legend, add a selector-specific CSS rule to suppress only that generated heading for the sidebar conversation selector, without affecting other radio components elsewhere in the app.

4. `feat(chat-ui): align sidebar list height with the chat transcript area`
- Adjust the desktop layout/CSS so the sidebar conversation list height is based on the visible chat transcript panel rather than the entire main column down to the composer.
- Keep only one active scroll surface for the conversation list.
- Preserve the current top controls (`Ny samtale`, mode selector, `Start ny samtale`, `Oppdater`) above the scroll area and keep the conversation count below it.

5. `refactor(chat-ui): preserve bounded behavior on narrow layouts`
- Keep the mobile/narrow-screen max-height behavior, but ensure it applies only at the breakpoint and does not leak into desktop sizing.
- Verify the sidebar remains visually balanced when references are open or closed.

6. `test(chat-ui): cover label suppression and sidebar height selectors`
- Update `tests/test_chat_page_ui.py` to assert:
  - the conversation selector uses the label-suppression hook/config
  - the sidebar transcript-height hooks exist
  - the CSS contains the selector-specific rule that hides the generated radio heading
  - the desktop height rule targets the sidebar conversation region rather than only a generic full-height column
  - the narrow-layout bounded rule is still present
- Re-run the existing chat UI/sidebar/reference suites to confirm no regressions.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py tests/test_chat_sidebar_loading_ui.py`
- `pytest` after targeted chat/UI suites pass
- Manual UI check:
  - `Radio` is no longer visible above the conversation list
  - desktop: the list stops around the bottom of the visible chat transcript area, not at the `Send` button
  - desktop: scrolling still reaches all conversations
  - narrow layout: the list remains bounded and scrollable
  - references open/closed does not break sidebar height alignment

## Assumptions and Defaults
- The `Radio` text is an unwanted generated component label and should be fully hidden, not replaced with another heading.
- The desired desktop alignment target is the chat transcript region above the composer, not the entire right column.
- No backend, pagination, or state changes are required; this is a chat-page structure/CSS cleanup.
