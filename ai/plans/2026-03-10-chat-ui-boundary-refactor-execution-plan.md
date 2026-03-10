# Multi-Commit Plan: Chat UI Boundary Refactor

## Summary
Refactor chat UI incrementally so it matches the project’s page architecture, while preserving behavior and keeping each commit small, testable, and reversible. The goal is to make `src/ui/pages/chat_page.py` thin, move orchestration out of the page file, and move event wiring ownership to `src/ui/main_app.py`.

## Commit Plan
1. `docs(plan): add chat refactor execution plan + baseline checks`
   Save this plan to `ai/plans`, then run targeted baseline tests (`test_chat_scope_ui`, `test_chat_references_ui`, `test_chat_entry_bootstrap_ui`, `test_conversation_service_sources`) to lock current behavior before refactor.

2. `refactor(chat): introduce typed chat state/contracts`
   Add a dedicated chat types/state module (`ChatConversationState`, `ChatSourceEntry`, `ChatTurn`, state constructors/converters) and migrate internal chat logic to those helpers without changing handler outputs yet.

3. `refactor(chat): extract chat orchestration service`
   Move API orchestration/pagination/normalization flow out of page code into a dedicated service module built on `conversation_service` (fetch conversations, fetch full message history, create/send flows, sidebar refresh model). Keep behavior and status text identical.

4. `refactor(chat): split handlers from page construction`
   Move event handlers into `chat_handlers.py`; keep `chat_page.py` as a thin facade that builds components and exposes required refs/states. Provide temporary compatibility re-exports so existing tests remain stable during transition.

5. `refactor(ui): move chat event wiring to main app + cleanup`
   Remove `.click/.change/.submit` wiring from chat page builder and wire chat events in `main_app.py`, consistent with the architecture guide. Then remove compatibility shims that are no longer needed and trim `chat_page.py` to component assembly only.

6. `test/chore: finalize refactor and verify full suite`
   Run `pytest`, `ruff check src tests`, and `mypy src`; fix any regressions from the boundary changes. Final acceptance target: `chat_page.py` focused on UI composition, handlers/services split by responsibility, no behavior regressions.

## Public Interfaces / Type Changes
- `ChatPageComponents` will be expanded to expose all controls/states needed for external wiring in `main_app.py` (buttons/selectors/chatbot/textbox + local chat states).
- Add internal chat-specific typed contracts for conversation/source/history state to eliminate ad-hoc dict handling.
- No FastAPI endpoint/schema changes and no wire-protocol changes between UI and API.

## Test Plan
1. Per-commit targeted tests for chat UI logic:
   `pytest tests/test_chat_scope_ui.py tests/test_chat_references_ui.py tests/test_chat_entry_bootstrap_ui.py tests/test_conversation_service_sources.py`
2. After commit 5: broader conversation flow coverage:
   `pytest tests/test_conversation_flow.py tests/test_conversations.py`
3. Final gate:
   `pytest`
   `ruff check src tests`
   `mypy src`

## Assumptions and Defaults
- Default priority is behavior parity, not feature work.
- Existing Norwegian UI/status strings remain unchanged unless a test proves current text is incorrect.
- No backend/API redesign is done in this refactor; this is a UI boundary and maintainability refactor.
- If a commit risks broad breakage, keep compatibility wrappers one extra commit and remove them only after tests pass.
