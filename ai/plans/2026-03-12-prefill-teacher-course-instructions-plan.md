# Prefill Teacher Course Instructions

## Summary
- Use the existing backend endpoint `GET /courses/{course_id}/instructions` as the source of truth for the teacher-course instructions textbox.
- When a teacher opens the course page, preload the textbox with the saved `course_specific_instructions`, keep the character counter in sync, and leave the status area empty on success.
- On preload failure, keep the textbox empty and show an inline error in the existing status area. No database or schema change is needed.

## Commit Plan
1. Add the read path and lock the contract
- In `src/ui/services/course_service.py`, add a read helper for the existing instructions endpoint with the same success/error style as the other UI service helpers.
- Add or extend tests so the read contract is explicit: authorized teachers get the current instructions, and current 403/404 behavior stays unchanged.

2. Hydrate the teacher instructions tab from persisted data
- Refactor `src/ui/pages/teacher_course_tabs/instructions_tab.py` so the teacher-course page gets textbox value, counter text, and status from one preload helper instead of the current hard-coded empty resets.
- Wire `src/ui/main_app.py` to call that preload helper during teacher-course rendering, so the textbox shows the current instructions by default and the counter reflects the loaded text length.
- Keep save behavior intact: trim before save, show the cleaned saved value after success, and continue clearing the field when the stored instructions are empty.

3. Add regression coverage for the new default-load behavior
- Extend `tests/test_teacher_course_instructions_ui.py` to cover preload success, preload with no saved instructions, missing course/token, and fetch errors.
- Add one render/open-flow test proving that opening a responsible course with saved instructions ends with the textbox prefilled and the counter synced, without requiring manual input.

## Interface Changes
- New UI service helper: `get_course_instructions(token, course_id)`.
- Replace the current write-only reset helpers with one internal preload helper that returns textbox update, counter text, and status together.
- No FastAPI API surface change; the UI will start consuming the existing read endpoint.

## Test Plan
- Teacher with saved instructions sees them immediately in the textbox.
- Teacher with no saved instructions sees an empty textbox and `0/3000`.
- Expired token or unauthorized access leaves the field empty and shows an inline status error.
- Saving trimmed text after preload still updates the textbox and counter correctly.

## Assumptions
- The desired default is the latest persisted instruction value each time the teacher-course page is rendered, not a cached client-only value.
- Reusing the existing backend endpoint is preferred over adding a new route because the server-side read path already exists.
