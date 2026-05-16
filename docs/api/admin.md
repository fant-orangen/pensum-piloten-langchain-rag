# Admin API

Router: `src/api/routers/admin.py`

Schemas: `src/api/schemas/admin.py`

All endpoints require `get_current_app_user()`.

Additional admin service rule:

- caller must have `global_role="admin"`;
- when `ADMIN_EMAIL` is configured, caller email must match `ADMIN_EMAIL`.

## Endpoints

| Method | Path | Response |
|---|---|---|
| `GET` | `/admin/users` | `list[AdminUserRead]` |
| `POST` | `/admin/users/{user_id}/promote-teacher` | `AdminUserRead` |
| `POST` | `/admin/users/{user_id}/demote-student` | `AdminUserRead` |

## `AdminUserRead`

Fields:

| Field | Type |
|---|---|
| `id` | UUID |
| `email` | string |
| `first_name` | string |
| `last_name` | string |
| `global_role` | string |
| `is_course_owner` | boolean |

`is_course_owner` is computed by checking whether the user appears as `course.created_by_id`.

## `GET /admin/users`

Returns all users ordered by email.

## `POST /admin/users/{user_id}/promote-teacher`

Sets `global_role="teacher"`.

Errors:

- `400` when target user is admin;
- `404` when target user does not exist;
- `409` when target user is already teacher.

## `POST /admin/users/{user_id}/demote-student`

Sets `global_role="student"` and removes course enrollments where the target user has role `teacher`.

Errors:

- `400` when target user is admin;
- `404` when target user does not exist;
- `409` when target user is already student;
- `409` when target user created any course.

