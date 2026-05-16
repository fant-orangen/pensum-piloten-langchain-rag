# Courses API

Router: `src/api/routers/courses.py`

Schemas: `src/api/schemas/course.py`

All endpoints require `get_current_app_user()`.

## Course Endpoints

| Method | Path | Required access | Response |
|---|---|---|---|
| `GET` | `/courses` | authenticated app user | `list[CourseRead]` |
| `GET` | `/courses/available` | authenticated app user | `list[CourseRead]` |
| `GET` | `/courses/responsible` | platform teacher/admin | `list[CourseRead]` |
| `GET` | `/courses/all-teachers` | platform teacher/admin | `list[CourseStudentRead]` |
| `GET` | `/courses/{course_id}` | enrolled user or admin | `CourseSummaryRead` |
| `POST` | `/courses` | platform teacher/admin | `CourseRead` |
| `DELETE` | `/courses/{course_id}` | course creator/admin | `204 No Content` |

### `CourseRead`

Returned by course management endpoints.

Fields:

- `id`
- `name`
- `code`
- `rag_mode`
- `chroma_collection`
- `course_specific_instructions`
- `index_version`
- `rebuild_status`
- `rebuild_error`
- `created_by_id`

### `CourseSummaryRead`

Returned by `GET /courses/{course_id}` for chat/navigation.

Fields:

- `id`
- `name`
- `code`

### `POST /courses`

Request:

```json
{
  "name": "Operating Systems",
  "code": "TDT4186",
  "documents_dir": "",
  "rag_mode": "kg_rag",
  "course_specific_instructions": null
}
```

Behavior:

- creates the course;
- creates the course material directory from `code`;
- enrolls the creator as course `teacher`;
- sets `chroma_collection=null`;
- returns `409` when `code` already exists.

`documents_dir` is accepted by the schema. The service derives the actual directory from course code.

## Students and Teachers

| Method | Path | Required access | Response |
|---|---|---|---|
| `GET` | `/courses/{course_id}/students` | course teacher/admin | `Page[CourseStudentRead]` |
| `GET` | `/courses/{course_id}/teachers` | course creator/admin | `Page[CourseStudentRead]` |
| `POST` | `/courses/{course_id}/enrollments` | course teacher/admin | `EnrollmentRead` |
| `DELETE` | `/courses/{course_id}/enrollments` | course teacher/admin | `{"removed": number}` |
| `DELETE` | `/courses/{course_id}/enrollments/{user_id}` | course teacher/admin for students; course creator/admin for teachers | `204 No Content` |

### `GET /courses/{course_id}/students`

Query parameters:

| Parameter | Type | Constraint |
|---|---|---|
| `page` | integer | default `1`, minimum `1` |
| `page_size` | integer | default `20`, range `1..100` |
| `search` | string | optional |

`search` matches `first_name`, `last_name`, or `email` case-insensitively.

### `POST /courses/{course_id}/enrollments`

Request:

```json
{
  "user_email": "student@example.com",
  "role": "student"
}
```

Behavior:

- looks up an existing user by email;
- creates an enrollment if none exists;
- changes existing enrollment role when the user is already enrolled with a different role;
- returns `409` when the same user is already enrolled with the same role;
- returns `404` when the target user does not exist.

### `DELETE /courses/{course_id}/enrollments`

Removes all student enrollments from the course. Teacher enrollments are not removed.

### `DELETE /courses/{course_id}/enrollments/{user_id}`

Rules:

- course teachers/admins can remove student enrollments;
- course creator/admin can remove teacher enrollments;
- removing the course owner returns `409`.

## Enrollment Import

| Method | Path | Required access | Response |
|---|---|---|---|
| `POST` | `/courses/{course_id}/enrollment-imports/preview` | course teacher/admin | `EnrollmentImportPreviewRead` |
| `POST` | `/courses/{course_id}/enrollment-imports/{preview_id}/confirm` | preview creator/admin | `EnrollmentImportConfirmRead` |
| `DELETE` | `/courses/{course_id}/enrollment-imports/{preview_id}` | preview creator/admin | `204 No Content` |

### CSV Preview

Input: multipart file named `file`.

CSV parsing rules:

- UTF-8 with optional BOM is accepted;
- first column is email;
- second column is first name;
- third column is last name;
- optional header row is detected from the first non-empty row;
- duplicate emails are reported once;
- invalid emails are reported.

Preview behavior:

- does not create enrollments;
- replaces any previous preview by the same user for the same course;
- stores accepted emails and parsed names in `enrollment_import_preview`;
- returns `400` when the CSV is not UTF-8 or contains no valid email rows.

### CSV Confirm

Confirm behavior:

- re-classifies candidates before mutation;
- creates missing users with `must_change_password=true`;
- enrolls eligible users;
- deletes the preview row;
- returns `409` if a concurrent enrollment change triggers an integrity error.

### CSV Cancel

Deletes the preview row without changing enrollments.

## Documents and Rebuilds

| Method | Path | Required access | Response |
|---|---|---|---|
| `GET` | `/courses/{course_id}/documents` | course teacher/admin | `list[CourseDocumentRead]` |
| `POST` | `/courses/{course_id}/documents` | course teacher/admin | `list[CourseDocumentRead]` |
| `POST` | `/courses/{course_id}/documents/zip` | course teacher/admin | `ZipImportResultRead` |
| `DELETE` | `/courses/{course_id}/documents` | course teacher/admin | `{"removed": number}` |
| `DELETE` | `/courses/{course_id}/documents/{document_id}` | course teacher/admin | `204 No Content` |
| `GET` | `/courses/{course_id}/documents/status` | course teacher/admin | `CourseMaterialsStatusRead` |
| `POST` | `/courses/{course_id}/documents/confirm` | course teacher/admin | `202 CourseMaterialsStatusRead` |

Upload and zip safety details are documented in `docs/security/upload-safety.md`.

Document status values:

| Status | Meaning |
|---|---|
| `pending_add` | Staged for next rebuild. |
| `active` | Included in active material index. |
| `pending_remove` | Excluded from next rebuild and deleted after activation. |

Rebuild status values:

| Status | Meaning |
|---|---|
| `idle` | No rebuild running. |
| `queued` | Rebuild has been queued by confirm endpoint. |
| `building` | Background rebuild task is running. |
| `failed` | Last rebuild failed; `rebuild_error` contains the error text. |

### `POST /courses/{course_id}/documents/confirm`

Behavior:

- returns `400` when there are no staged changes;
- returns `409` when a rebuild is already `queued` or `building`;
- sets `rebuild_status=queued`;
- schedules `run_course_material_rebuild()` as a FastAPI background task;
- returns HTTP `202`.

## Course Instructions

| Method | Path | Required access | Response |
|---|---|---|---|
| `GET` | `/courses/{course_id}/instructions` | course teacher/admin | `CourseInstructionsRead` |
| `PATCH` | `/courses/{course_id}/instructions` | course teacher/admin | `CourseRead` |

Patch request:

```json
{
  "course_specific_instructions": "Use concise examples from the lecture notes."
}
```

Blank text clears existing instructions.
