# CSV Student Import on Teacher Course Page

## Summary
- Add a CSV import flow on the teacher course page so a teacher can upload a `.csv` file of email addresses and import multiple students in one action.
- Keep this frontend-only in the first pass: parse the CSV locally and reuse the existing single-student enrollment API once per valid email.
- For unregistered emails, continue processing the file, show a short warning popup with the count, and keep the full missing-email list in the persistent import-results area.
- Ship this in 3 commits so each commit is coherent and reviewable.

## Implementation Changes
- Commit 1: Student import UI shell
  - Extend the teacher course page with a dedicated CSV import subsection under `## Studenter`, separate from the existing single-email textbox/button.
  - Add three new UI elements: a `gr.File(type="filepath")` for `.csv`, an `Importer studenter` button, and a dedicated Markdown area for import results.
  - Add teacher-facing copy describing the accepted format: one email per row, optional header, blank lines ignored.
  - Wire the new controls through the main app event bindings.
  - Reset the CSV input and import-results Markdown whenever the teacher course page is freshly rendered so results from one course do not leak into another.
- Commit 2: CSV parsing and bulk import flow
  - Add a new teacher-course handler that accepts `(state, csv_path)` and returns updates for the CSV input, student list, import-results Markdown, and the existing generic status message.
  - Parse the uploaded file with Python’s `csv` module from the filepath returned by Gradio.
  - Parsing rules for v1:
    - Read as `utf-8-sig` so BOM-prefixed CSVs work.
    - Use only the first column.
    - Treat the first non-empty row as a header only when the first cell matches one of: `email`, `e-mail`, `epost`, `e-post`, `user_email`.
    - Trim whitespace around each email.
    - Ignore blank rows.
    - Deduplicate emails within the file while preserving first occurrence.
  - Validate emails before calling the API; invalid rows are skipped and reported with row numbers.
  - For each unique valid email, call the existing `enroll_user()` frontend service sequentially.
  - Refresh the student list once after the import run completes, not after each email.
  - Build a structured import summary with counts for imported successfully, already enrolled, user not found, invalid CSV rows, and other API failures.
  - When one or more users are not registered, trigger a toast-style `gr.Warning()` with the count and direct the teacher to the import-results area for the full list.
  - Keep the full missing-email list in the persistent import-results Markdown, alongside other row-level failures.
  - Show up to 10 detailed row/error lines in the import-results Markdown and collapse the rest into a final “and N more” line.
  - Keep the existing single-email add flow unchanged.
- Commit 3: Hardening and polish
  - Make the generic status text short and action-level, for example: `Import fullført med delvise feil.`
  - Keep detailed per-row feedback only in the import-results Markdown so long CSV failures do not overwhelm the shared status area.
  - Add defensive handling for missing course id, missing auth token, no file selected, wrong file extension, empty CSV after filtering blanks/header, and all rows invalid or all enrollments rejected.
  - Align any stale tests or helper expectations so student management now explicitly covers both single-email add and CSV import on the same page.
