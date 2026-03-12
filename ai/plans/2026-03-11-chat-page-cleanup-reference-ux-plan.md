# Chat Page Cleanup and Reference UX Plan

## Summary
- The current chat page already separates concerns reasonably: page layout lives in `build_chat_page`, source selection stays in chat handlers, and reference markup is generated in the reference render helpers.
- The messy part is mostly presentation: the references area is always exposed, every source shows full text immediately, and excerpt text is not normalized into readable plain text before rendering.
- No backend, API, database, or retrieval changes are needed. This is a frontend-only rollout.

## Important Interface Changes
- Add a dedicated `CHAT_PAGE_CSS` export and include it in the main Gradio app CSS bundle.
- Extend `ChatPageComponents` with a handle for the overall references accordion/container so layout and tests can target it directly.
- Keep the existing handler output contract intact: handlers still return `references_panel` HTML and `references_status` text. Only the rendered HTML structure changes.

## Commit Plan
1. `docs(plan): add chat page cleanup rollout plan`
- Save this plan under `ai/plans` with today’s date and a chat-page-specific filename.
- Note the chosen defaults: broader page polish, readable plain-text excerpts, overall references section collapsible but open by default.

2. `refactor(chat-ui): add dedicated chat page layout hooks and css bundle`
- Introduce `CHAT_PAGE_CSS` for the chat page instead of relying on unrelated page CSS.
- Add stable `elem_id` / `elem_classes` hooks for the sidebar, main chat column, composer area, and references area.
- Export `CHAT_PAGE_CSS` through `src.ui.pages` and append it in `build_main_app()`.

3. `feat(chat-ui): restyle the chat page and make kildereferanser collapsible`
- Wrap the references section in a `gr.Accordion` labeled `Kildereferanser`, `open=True`.
- Polish the page structure so the three regions read as intentional cards/panels with better spacing, hierarchy, and responsive stacking.
- Keep the existing sidebar and chat behavior unchanged; this commit is layout and visual polish only.

4. `feat(chat-references): render expandable source cards with cleaned excerpts`
- Move excerpt cleanup to source normalization in the conversation service: decode HTML entities, strip HTML tags, collapse noisy whitespace, preserve useful line breaks, then truncate consistently.
- Change reference rendering so each source becomes a collapsed `<details>` card by default.
- Use the summary row to show the source identity first: document name and page.
- Show the cleaned excerpt only inside the expanded body.
- Preserve current empty/error/selection behavior: latest assistant sources still appear automatically, user-message selection still clears the panel, and fallback statuses remain.

5. `test(chat-ui): lock new reference and layout behavior`
- Update chat page construction tests for the new accordion/container hooks.
- Update reference rendering tests to assert:
  - one `<details>` per source
  - excerpts are hidden by default
  - summary rows show document and page
  - cleaned text no longer exposes raw HTML tags/entities
  - existing empty/error/status flows still behave the same
- Add or update normalization tests for cleaned/truncated excerpts.

## Test Plan
- `pytest tests/test_chat_page_ui.py tests/test_chat_references_ui.py tests/test_conversation_service_sources.py`
- `pytest tests/test_chat_scope_ui.py tests/test_chat_entry_bootstrap_ui.py`
- `pytest` after the targeted chat/UI suites pass

## Assumptions and Defaults
- `Kildereferanser` is user-collapsible but starts open by default.
- Each individual source excerpt starts collapsed by default.
- Excerpt readability cleanup happens only on the frontend normalization path; backend payloads stay unchanged.
- Existing status strings should stay stable unless a test-backed wording change is necessary for clarity.
