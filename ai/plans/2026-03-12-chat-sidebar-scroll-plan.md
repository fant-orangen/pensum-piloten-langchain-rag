# Make the Left Conversation List Scroll Inside the Sidebar

## Summary
- The conversation list on the left currently sits directly in the sidebar card, so a long list increases the page height instead of scrolling inside the panel.
- Change the sidebar to use the same structural pattern as the references area: fixed-height shell, dedicated inner scroll region, simple native scrollbar.
- Keep the top part of the sidebar (`Ny samtale`, mode selector, `Start ny samtale`, `Oppdater`) visible, and make only the conversation list section scroll.

## Important Interface Changes
- Extend `ChatPageComponents` with a dedicated wrapper/container for the scrollable conversation list area so layout and tests can target it directly.
- Keep the existing chat handler contract unchanged: `conversation_selector` and `conversation_count` still receive the same updates.
- No API, state schema, or handler-output changes are required unless a small UI-only wrapper component is added.

## Commit Plan
1. `docs(plan): add chat sidebar scroll plan`
- Save this plan under `ai/plans` with today’s date.
- Record the chosen defaults:
  - desktop sidebar gets an internal scroll area
  - mobile keeps the sidebar usable with a bounded max-height scroll region
  - only the conversation list section scrolls, not the whole sidebar card

2. `refactor(chat-ui): add sidebar list container hooks`
- Update `src/ui/pages/chat_page.py` to wrap `conversation_selector` and `conversation_count` in a dedicated sidebar-list section/container.
- Add stable `elem_id` / class hooks for:
  - the sidebar shell
  - the scrollable conversation list region
  - the footer/count area if it remains visually attached to the list
- Keep the rest of the sidebar structure unchanged.

3. `feat(chat-ui): make the conversation list scroll inside the sidebar`
- Add CSS so the sidebar card participates in the page height instead of expanding indefinitely.
- Make the conversation-list container the vertical scroll surface with `overflow-y: auto` and hidden horizontal overflow, styled similarly to the references panel.
- Ensure the new-conversation controls stay visible above the list while the list itself scrolls.
- On smaller screens, add a bounded max-height for the list so the sidebar remains compact and doesn’t dominate the page.

4. `refactor(chat-ui): align sidebar scroll behavior with workspace height`
- Tune the sidebar height behavior so it visually matches the chat/reference workspace rather than becoming taller than the main panel.
- Prevent double-scroll traps by keeping only the conversation-list region scrollable.
- Preserve existing responsive stacking behavior when the layout collapses on narrower screens.

5. `test(chat-ui): cover sidebar scroll hooks and layout selectors`
- Update `tests/test_chat_page_ui.py` to assert the new sidebar list container hook(s).
- Add CSS assertions for the new scroll selectors, including sidebar overflow/max-height rules.
- Re-run the existing chat page/reference UI tests to confirm the sidebar refactor does not disturb the adaptive main/reference layout.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat/UI suites pass
- Manual UI check:
  - many conversations: left list scrolls inside the sidebar
  - top controls remain visible while scrolling the list
  - page height no longer grows with the conversation count
  - mobile/narrow layout still works and the sidebar list has a bounded scroll area

## Assumptions and Defaults
- The scrollbar should be a simple native scrollbar, not a custom-styled widget.
- The `Oppdater` button stays above the scroll region with the new-conversation controls.
- The conversation count remains in the sidebar list section and can either scroll with the list or stay visually pinned at the bottom of that section, as long as the page no longer grows vertically.
- No backend or chat-state behavior changes are needed; this is a layout/CSS cleanup only.
