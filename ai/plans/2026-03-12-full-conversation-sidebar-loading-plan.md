# Show All Conversations in the Sidebar

## Summary
- The scrollbar issue is now separate from the data issue: the sidebar only loads the first page of conversations, so older conversations never reach the UI.
- The backend already supports paginated conversation listing and returns `total`; the frontend currently requests only `page=1&page_size=20` and then uses that partial result for both the selector choices and the count.
- Chosen behavior: auto-load all conversation pages in the frontend so the sidebar shows the full course-scoped history immediately.

## Important Interface Changes
- Keep `conversation_selector` as a `gr.Radio` and preserve all existing `.change()` wiring in `src/ui/main_app.py`.
- No backend route/schema changes are required if the existing `/conversations` pagination behaves as expected.
- Update the sidebar model/service layer so it works with the full fetched list and uses the backend `total` correctly instead of `len(first_page_items)`.

## Commit Plan
1. `docs(plan): add full conversation sidebar loading plan`
- Save this plan under `ai/plans` with today’s date.
- Record the chosen default: auto-load all conversation pages in the frontend.

2. `refactor(chat-service): add paginated conversation aggregation helper`
- Update `src/ui/services/chat_orchestration_service.py` to fetch all conversation pages for the selected course instead of only the first page.
- Use the backend `total` to stop paging deterministically.
- Keep ordering newest-first exactly as returned by the backend.

3. `feat(chat-sidebar): build selector choices and counts from the full conversation set`
- Update the sidebar model construction so:
  - selector choices include every fetched conversation
  - the summary count reflects the real total conversation count
  - selected conversation resolution still works when the chosen item is outside the old first page
- Keep all existing sidebar handler contracts unchanged unless a small internal type update is needed for the real total count.

4. `refactor(chat-ui): keep full-history loading compatible with bootstrap and refresh flows`
- Ensure bootstrap, refresh, load, and new-conversation flows all use the aggregated conversation fetch path consistently.
- Preserve current error handling and course scoping behavior.
- Avoid duplicate pagination logic across sidebar helpers.

5. `test(chat-sidebar): cover multi-page conversation loading`
- Add/extend tests for:
  - multiple `/conversations` page fetches being aggregated into one sidebar list
  - sidebar count showing the full total, not just the first page length
  - selecting/loading a conversation that appears on a later page
  - existing single-page behavior still working unchanged
- Update current chat bootstrap/scope tests where they assume a single page fetch signature.

## Test Plan
- `pytest tests/test_chat_entry_bootstrap_ui.py tests/test_chat_scope_ui.py tests/test_chat_page_ui.py`
- Add targeted service/sidebar tests for multi-page conversation aggregation
- `pytest tests/test_chat_references_ui.py`
- `pytest` after the targeted chat suites pass
- Manual UI check:
  - more than 20 conversations: all appear in the sidebar
  - scrollbar can reach the oldest conversation
  - count matches the real total
  - selecting an older conversation still loads it correctly

## Assumptions and Defaults
- No backend changes are required unless real testing shows `/conversations` has an undocumented cap or performance problem.
- Auto-loading all pages is acceptable for current conversation volumes.
- The sidebar remains newest-first and fully course-scoped.
- No visible pagination control will be added in this version.
