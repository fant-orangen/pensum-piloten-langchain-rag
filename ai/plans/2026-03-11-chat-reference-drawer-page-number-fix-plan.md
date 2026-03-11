# Chat Drawer and Page-Number Fix Plan

## Summary
- The current chat layout still reserves a full right column for references, so the chat area never regains that width even when references are collapsed.
- The page-number issue is upstream as well as frontend-facing: persisted and resolved sources currently rely almost entirely on `page`, while some loaders and source payloads may use other page-like keys or have no page at all.
- The target state is: full-width chat by default, references in a right-edge drawer that auto-opens when a tutor answer is selected, and page badges shown only when a real page value exists.

## Important Interface Changes
- Extend `ChatPageComponents` with explicit drawer controls/state handles for the references surface rather than a permanently allocated right-side workspace column.
- Keep the existing source-panel handler contract (`references_panel`, `references_status`) intact; add a separate drawer-open UI path instead of rewriting all chat outputs.
- Keep API schemas stable. `MessageSourceRead.page` remains a string, but backend/frontend normalization will accept additional page aliases and emit empty string when page is unavailable.

## Commit Plan
1. `docs(plan): add chat reference drawer and page-number fix plan`
- Save this plan in `ai/plans` with today’s date.
- Record the chosen defaults: right-edge drawer, auto-open on tutor-answer selection, hide page label when page is unavailable.

2. `refactor(chat-ui): separate references surface from the main chat workspace`
- Remove the dedicated references column from the normal chat layout in `chat_page.py`.
- Add a drawer trigger in the chat header/top actions and a dedicated drawer container anchored to the right edge of the page.
- Add drawer-specific CSS hooks so the main chat column expands to use the freed width by default.

3. `feat(chat-ui): add right-side references drawer behavior`
- Introduce lightweight frontend state/handlers for drawer open/close without changing the main chat send/load contracts.
- Auto-open the drawer when the user selects an assistant message with sources; keep it closed for user-message selections and empty-source states.
- Ensure the drawer can also be opened manually from the chat UI and closed explicitly without losing the current rendered sources.

4. `fix(sources): broaden page extraction and stop rendering fake unknown pages`
- Update backend source serialization/resolution in `messages.py` and `message_sources.py` to resolve page from a prioritized alias list such as `page`, `page_label`, `page_number`, and similar metadata fallbacks.
- Normalize page values consistently to display-safe strings and preserve empty string when no reliable page exists.
- Update frontend source normalization in `conversation_service.py` to read the same alias set so old and new payloads both render correctly.

5. `feat(chat-references): hide page chrome when page is absent`
- Update reference rendering so the summary badge and metadata row show page only when a non-empty normalized page exists.
- Remove the current `Ukjent` fallback from the visible reference card UI.
- Keep document and excerpt rendering unchanged except for the conditional page display.

6. `test(chat): cover drawer behavior and page normalization`
- Update chat-page UI tests for the new drawer hooks instead of a permanently present right column.
- Add handler tests for manual open/close and auto-open on assistant selection.
- Add normalization tests for page aliases and empty-page behavior in both frontend and backend source paths.
- Update reference rendering assertions so page badges/meta are absent when page is empty and present when page resolves correctly.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py tests/test_conversation_service_sources.py`
- Add targeted backend coverage for source-page extraction and resolved message sources, then run those tests alongside existing conversation/message tests.
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat/source suites pass

## Assumptions and Defaults
- The desired “go away to the right” behavior is an off-canvas right drawer, not a modal or below-chat section.
- Selecting a tutor answer with sources should auto-open the drawer.
- If a source still has no reliable page after alias-based extraction, the UI should hide page labels entirely rather than show `Side ukjent`.
- No retrieval, ranking, or database schema changes are required; this is a UI plus source-metadata normalization fix.
