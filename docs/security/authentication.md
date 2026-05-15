# Authentication and Authorization

This document is the source for authentication, authorization, and related security notes.

Source files:

- Auth routes: `src/api/routers/auth.py`
- Auth service: `src/api/services/auth.py`
- Token handling: `src/api/security.py`
- Dependencies: `src/api/dependencies.py`
- Authorization helpers: `src/api/utils/authorization_util.py`
- Admin service: `src/api/services/admin.py`
- Frontend auth context: `frontend/src/contexts/AuthContext.tsx`
- Frontend API client: `frontend/src/api/client.ts`
- Frontend route guard: `frontend/src/components/ProtectedRoute.tsx`

## JWT

| Property | Current implementation |
|---|---|
| Algorithm | `HS256` |
| Signing key | `SECRET_KEY` from settings |
| Token subject | User UUID string in `sub` |
| Expiry | 24 hours |
| Transport | Bearer token in `Authorization` header |
| Current user lookup | `get_current_user()` |

`get_current_user()` rejects:

- invalid or expired JWTs;
- JWT subjects that are not valid UUIDs;
- missing users;
- inactive users.

Production requirements:

- Set `SECRET_KEY` to a long random value.
- Rotate `SECRET_KEY` if it is exposed.
- Use HTTPS for every browser-to-server request.

## Passwords

| Operation | Behavior |
|---|---|
| Register | Hashes password with bcrypt before storing. |
| Login | Verifies plaintext password against stored bcrypt hash. |
| Change password | Replaces stored hash with a new bcrypt hash. |

Schema constraints:

- registration password: minimum 8 characters;
- new password in change-password request: minimum 8 characters.

Plaintext passwords are accepted only by:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/change-password`

## Imported Users

CSV enrollment import can create user rows with:

```text
hashed_password = ""
must_change_password = true
```

Security boundary:

- `get_current_user()` accepts the user after login.
- `get_current_app_user()` blocks normal application endpoints while `must_change_password=true`.
- `/auth/change-password` clears `must_change_password` after setting a bcrypt hash.

Frontend flow:

1. User logs in.
2. `ProtectedRoute` redirects to `/settings`.
3. User changes password.
4. Backend clears `must_change_password`.

## Roles

Platform role is stored on `app_user.global_role`.

| Role | Backend meaning |
|---|---|
| `student` | Can use enrolled courses and own conversations. |
| `teacher` | Can create courses and manage courses where enrolled as teacher. |
| `admin` | Passes admin checks and course teacher checks. |

Course role is stored on `course_enrollment.role`.

| Role | Backend meaning |
|---|---|
| `student` | Can create and use conversations for the course. |
| `teacher` | Can manage course students, materials, and instructions. |

Course role is independent from platform role.

## Backend Authorization Helpers

| Helper | Allows |
|---|---|
| `require_teacher_or_admin(user)` | Platform `teacher` or `admin`. |
| `require_admin(user)` | Platform `admin`. |
| `require_course_owner_or_admin(user, created_by_id)` | Course creator or platform `admin`. |
| `require_course_teacher_or_admin(user, course_id, db)` | Course teacher enrollment or platform `admin`. |
| `require_unenroll_permission(...)` | Teacher/admin for students; creator/admin for teachers. |

## Conversation Access

| Operation | Check |
|---|---|
| List conversations | Current user's conversations only. |
| Create conversation | Course exists and current user is enrolled in the course. |
| Read messages | Conversation belongs to current user. |
| Send message | Conversation belongs to current user. |
| Rename conversation | Conversation belongs to current user. |
| Delete conversation | Conversation belongs to current user. |
| Read message sources | Conversation belongs to current user. |

## Course Management Access

| Operation group | Required access |
|---|---|
| Create course | Platform `teacher` or `admin`. |
| Responsible courses | Platform `teacher` or `admin`; returns courses where user has course teacher enrollment. |
| Students list and enrollment changes | Course teacher or admin. |
| Course materials | Course teacher or admin. |
| Course instructions | Course teacher or admin. |
| Teacher list | Course creator or admin. |
| Course deletion | Course creator or admin. |

## Admin User Management

Admin user management requires:

1. platform role `admin`;
2. if `ADMIN_EMAIL` is configured, current user's email must match it.

Admin user management can:

- list users;
- promote users to platform `teacher`;
- demote platform `teacher` users to `student`.

Demotion is rejected when the target user created any course.

## Frontend Token Storage

The frontend stores the access token in `localStorage` under `access_token`.

`apiClient` behavior:

- request interceptor attaches `Authorization: Bearer <token>`;
- 401 response interceptor removes `access_token` and redirects to `/login`;
- login requests are excluded from the 401 redirect branch.

Security consequence:

- A script running in the browser origin can read the token from `localStorage`.
- Do not rely on `localStorage` as protection against XSS.

## Frontend Route Guard

`ProtectedRoute` applies these rules:

| Condition | Result |
|---|---|
| User is not loaded yet | Show spinner. |
| No authenticated user | Redirect to `/login`. |
| `must_change_password` and path is not `/settings` | Redirect to `/settings`. |
| Platform `admin` and path is not `/dashboard/admin` | Redirect to `/dashboard/admin`. |
| Required role is higher than user role | Redirect to `/`. |

The frontend guard is not the security boundary. Backend dependencies and service checks enforce access.

## Not Implemented

These mechanisms are not present in the current code:

- refresh tokens;
- token revocation list;
- multi-factor authentication;
- account lockout after repeated failed logins;
- API rate limiting for auth endpoints;
- password complexity rules beyond the 8-character minimum.
