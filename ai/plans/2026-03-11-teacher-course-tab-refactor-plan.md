# Teacher Course Page Tab Refactor

## Summary
- Restructure the teacher course page into a compact header plus 3 tabs: `Studenter`, `Kursmateriale`, and `Kursinstruksjoner`.
- Move `Tilbake` to the top-left in a shared header, keep the course title in the header, and keep `Se som student` as a header-level secondary action.
- Keep one root teacher-course page module, but extract each tab into its own module so layout and handlers are easier to maintain.
- Default the page to the `Studenter` tab whenever a teacher opens a course page.
- Replace the single shared status area with per-tab status/output areas.

## Implementation Changes
- Commit 1: Header and tab scaffold
  - Replace the current tall vertical layout with a page header row containing `Tilbake`, course title, and `Se som student`.
  - Introduce native `gr.Tabs` with three tabs in the teacher course page root.
  - Move existing student controls into the `Studenter` tab, material and ingestion controls into `Kursmateriale`, and instructions controls into `Kursinstruksjoner`.
  - Preserve existing behavior and handler wiring in this commit; this is a structural layout pass only.
  - Set `Studenter` as the default active tab when the teacher course page renders.
- Commit 2: Extract tab modules
  - Keep `teacher_course_page.py` as the root/composition module responsible for shared header controls, top-level page dataclass, and shared state helpers.
  - Extract student management UI/handlers into a dedicated module.
  - Extract course materials and ingestion UI/handlers into a dedicated module.
  - Extract course instructions UI/handlers into a dedicated module.
  - Keep public imports stable through `src/ui/pages/__init__.py` so `src/ui/main_app.py` only needs minimal wiring updates.
- Commit 3: Status and rendering cleanup
  - Replace the single teacher-course status Markdown with one status/output area per tab.
  - Scope feedback so student add/import messages stay in `Studenter`, upload/delete/ingestion messages stay in `Kursmateriale`, and prompt save messages stay in `Kursinstruksjoner`.
  - Keep the CSV import result panel inside `Studenter` and do not mirror that detail elsewhere.
  - Ensure render/reset helpers initialize each tab cleanly when changing course or returning to the page.
- Commit 4: Layout polish
  - In `Studenter`, separate “add one student” and “import CSV” into clearly separated sections.
  - In `Kursmateriale`, visually separate source-material management from ingestion controls.
  - In `Kursinstruksjoner`, keep the helper text close to the textbox and reduce excess vertical spacing.
  - Normalize button hierarchy so primary actions are visually obvious and secondary actions do not compete with them.
