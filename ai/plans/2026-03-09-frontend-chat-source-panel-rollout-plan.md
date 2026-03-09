# Frontend-Only Chat Source Panel Rollout Plan (2026-03-09)

## Goal
Add a right-side references panel in chat where the user can select a tutor reply and inspect source references used for that reply.

## Scope
- Frontend/UI client changes only.
- No backend, chain, schema, or database changes.
- Existing chat behavior remains intact if source data is absent.

## Dependency contract (backend-owned)
The frontend expects assistant messages from conversation endpoints to include `sources` when available.

Accepted shapes (frontend will normalize):
- Structured objects (preferred):
  - `{"document": str, "page": str|int|None, "excerpt": str}`
- Legacy/temporary object fields (fallback):
  - `source_file`, `filename`, `file`, `source`
  - `page`
  - `text`, `content`, `excerpt`, `chunk`, `snippet`
- Legacy strings:
  - `"filename.pdf"`

When fields are missing, frontend will render safe placeholders and keep the chat usable.

## Implementation slices
1. UI service normalization
- Add source normalization in the conversation UI service.
- Normalize `sources` for both:
  - `GET /conversations/{id}/messages`
  - `POST /conversations/{id}/messages`
- Keep return shape stable for callers.

2. Chat page source-aware state + panel
- Keep existing visible `gr.Chatbot(type="messages")` history.
- Add parallel internal state with per-message `sources`.
- Add right-side panel with columns:
  - `Dokument`
  - `Side`
  - `Utdrag`
- Auto-populate panel with latest assistant reply after:
  - loading a conversation
  - sending a new message

3. Reply selection wiring
- Use `chatbot.select(...)` to map selected message -> source panel rows.
- If selected message is not assistant, clear panel with guidance text.
- If assistant has no sources, show explicit empty-state message.

4. Tests
- Unit tests for source normalization and excerpt truncation safety.
- Chat handler tests for:
  - load/send source-state propagation
  - selected assistant reply populates panel
  - selected user reply clears panel
  - absent backend sources fallback
- Re-run existing chat scope tests.

## Acceptance criteria
- Users can click a tutor reply and see its reference rows in right panel.
- Panel shows `Dokument`, `Side`, and a short excerpt.
- UI does not crash if `sources` is missing or malformed.
- Existing chat scope protections continue to pass tests.
