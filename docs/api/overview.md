# API Overview

The backend API is a FastAPI application mounted in `src/api/app.py`.

Base route groups:

| Prefix | Router | Purpose |
|---|---|---|
| `/auth` | `src/api/routers/auth.py` | Registration, login, current user, password change. |
| `/courses` | `src/api/routers/courses.py` | Courses, materials, enrollment, course instructions. |
| `/conversations` | `src/api/routers/conversations.py` | Course-scoped conversations, messages, sources. |
| `/preferences` | `src/api/routers/preferences.py` | User prompt mode preference. |
| `/admin` | `src/api/routers/admin.py` | Admin user management. |
| `/health` | `src/api/app.py` | Liveness check. |

## Authentication

Protected endpoints use Bearer JWT authentication.

```http
Authorization: Bearer <access_token>
```

The `/admin`, `/courses`, `/conversations`, and `/preferences` routers use `get_current_app_user()`. That dependency rejects users with `must_change_password=true`.

`/auth/me` and `/auth/change-password` use `get_current_user()`. Forced-password-change users can call those endpoints.

## Response Conventions

JSON responses use Pydantic schemas from `src/api/schemas/`.

Paginated endpoints return:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0
}
```

Pagination parameters:

| Parameter | Constraint |
|---|---|
| `page` | integer, minimum `1` |
| `page_size` | integer, minimum `1`, maximum `100` |

## Error Shape

FastAPI errors use the standard response shape:

```json
{
  "detail": "Error message"
}
```

`stage_error()` returns a string detail with a bracketed code:

```text
[message_agent_response_failed] Failed to obtain a response from the tutor agent.
```

See `docs/api/errors.md` for common status codes.

## Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```
