# Chat Entry Regression Fix Plan (2026-03-09)

## Problem Summary
Users can enter Chat and see stale UI state with an empty conversation list. In some entry paths, sending the first message appears to do nothing because no active conversation exists and the handler exits early.

## Root Cause
1. Chat initialization currently depends on `token_state.change` and `course_id_state.change` only.
2. Route changes to `chat` can happen without token/course value changes, so initialization may not run.
3. First send path requires a selected conversation ID and returns early if missing.

## Behavior Contract
1. Entering route `chat` must always reset local chat state and refresh sidebar from backend.
2. If no active course is set, frontend auto-selects the first enrolled course from `/courses`.
3. If no enrolled courses exist, chat stays empty and shows a clear status message.
4. If user sends a message with an active course but no conversation selected, frontend auto-creates a conversation and sends the message in the same handler call.

## Acceptance Criteria
- Conversation selector is populated on chat route entry when user has enrolled courses.
- Open-conversation label and visible history are cleared on route entry unless user explicitly loads a conversation.
- First message send works even when no conversation was manually created.
- Existing course-scope protections still block cross-course stale conversation usage.
- No backend API changes required.
