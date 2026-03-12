# Fix Sidebar Conversation List Height and Scrolling

## Summary
- The current sidebar conversation list has two problems:
  - its visible height is capped in a way that does not align with the main chat workspace
  - the list is not actually scrollable, even though it now sits inside a dedicated wrapper
- Keep the conversation list as a `gr.Radio`, but add explicit hooks and CSS overrides for the Gradio radio internals so the sidebar behaves like a real scroll panel.
- The target state is:
  - desktop: sidebar list fills the remaining sidebar height and scrolls internally
  - narrow/mobile layouts: sidebar remains usable with a bounded internal scroll area
  - the rest of the page height no longer grows with the number of conversations

## Important Interface Changes
- Extend the chat page UI hooks with an explicit `elem_id` for the conversation selector itself, not just the outer list container.
- Keep the existing handler/event contract unchanged:
  - `conversation_selector` remains a `gr.Radio`
  - all `.change()` wiring in `src/ui/main_app.py` stays intact
- No API, state, or chat-handler output changes are needed.

## Commit Plan
1. `docs(plan): add sidebar height and scroll fix plan`
- Save this plan under `ai/plans` with today’s date.
- Record the chosen defaults:
  - keep `gr.Radio`
  - desktop uses full remaining sidebar height
  - narrow layouts keep an internal bounded scroll area

2. `refactor(chat-ui): add explicit selector hooks for sidebar scrolling`
- Update `src/ui/pages/chat_page.py` to give the conversation selector its own stable `elem_id`, in addition to the existing sidebar shell/list container hooks.
- Keep the current sidebar structure, but make the selector targetable separately from the outer scroll wrapper.
- Do not change any event wiring or handler signatures in this commit.

3. `feat(chat-ui): make the sidebar list actually scroll on desktop`
- Remove the desktop misalignment by letting the sidebar list section inherit the main workspace height rather than relying on an arbitrary cap.
- Add CSS that targets both:
  - the outer sidebar list container
  - the inner Gradio radio markup under the new selector `elem_id`
- Force the radio list surface to use `min-height: 0`, `height: 100%` where needed, and `overflow-y: auto` on the actual scrolling element so wheel/trackpad scrolling works.
- Keep the new conversation controls and `Oppdater` outside the scroll region.

4. `refactor(chat-ui): keep mobile scroll bounded without breaking desktop alignment`
- Restrict any `max-height` rule to the narrow-screen breakpoint only.
- Remove or replace any desktop height cap that makes the sidebar visually shorter than the chat/reference workspace.
- Ensure only one scroll surface exists for the sidebar list to avoid nested-scroll failures.
- Preserve the conversation count placement at the bottom of the sidebar section.

5. `test(chat-ui): lock sidebar scroll selectors and height rules`
- Update `tests/test_chat_page_ui.py` to assert:
  - the conversation selector has the new stable hook
  - the sidebar shell/list container hooks remain present
  - the CSS contains the selector-specific overflow/height rules
  - the desktop-only arbitrary cap is no longer asserted, while the narrow-screen bounded rule is
- Re-run the existing chat UI/reference UI suites to confirm the sidebar fix does not disturb the adaptive chat/reference layout.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after targeted chat suites pass
- Manual UI check:
  - desktop with many conversations: the left list scrolls with mouse wheel/trackpad
  - desktop: sidebar list bottom aligns with the main workspace instead of stopping early
  - desktop: page height does not grow with conversation count
  - narrow layout: sidebar list still has a bounded internal scroll region
  - selecting a conversation still triggers the existing load handler correctly

## Assumptions and Defaults
- The correct fix is to keep the `gr.Radio` and override its internal layout/overflow behavior, not replace it with a custom HTML list.
- Desktop should not have an arbitrary `max-height` on the conversation list; only narrow/mobile layouts should.
- The conversation count remains below the scrollable selector region.
- No backend or state changes are required; this is a chat-page layout/CSS fix.
