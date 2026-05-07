# Refactor DashboardPage.tsx

## Summary

Split `frontend/src/pages/DashboardPage.tsx` into focused dashboard modules while preserving behavior, layout, routes, role-based course visibility, course creation, and toast/error copy. Keep page-level auth, navigation, and query ownership in `DashboardPage.tsx`; move rendering-heavy pieces and dashboard-specific helpers into `frontend/src/pages/dashboard/`.

## Key Changes

- Create `frontend/src/pages/dashboard/` with focused modules for course cards, course sections, the create-course modal, course-code derivation, and dashboard query keys.
- Keep `DashboardPage.tsx` responsible for auth, navigation, role detection, modal visibility, React Query calls, create-course mutation, and query invalidation.
- Move the create-course mutation out of the modal so the modal receives `isSubmitting`, `errorMessage`, `onSubmit(payload)`, and `onClose`.
- Preserve all current navigation behavior and UI copy.

## Test Plan

- Run `npm run build` from `frontend/`.
- Run `git diff --check`.
- Inspect teacher/admin dashboard, student dashboard, course-card navigation, and create-course modal behavior.

## Assumptions

- This is a refactor-only pass with no API, route, schema, or feature changes.
- Query ownership stays in `DashboardPage.tsx`.
- The existing uncommitted `frontend/package-lock.json` change is unrelated and should remain untouched.
