# Authentication and Authorization

Authentication is JWT-based. Authorization uses platform roles and course-level enrollments.

Source files:

- Auth routes: `src/api/routers/auth.py`
- Auth service: `src/api/services/auth.py`
- Token handling: `src/api/security.py`
- Dependencies: `src/api/dependencies.py`
- Authorization helpers: `src/api/utils/authorization_util.py`
- Admin service: `src/api/services/admin.py`
- Frontend route guard: `frontend/src/components/ProtectedRoute.tsx`

## Authentication

Users authenticate with email and password.

| Step | Implementation |
|---|---|
| Password hashing | bcrypt in `hash_password()`. |
| Login verification | `authenticate_user()`. |
| Token creation | `create_access_token(subject=user.id)`. |
| Token algorithm | HS256. |
| Token expiry | 24 hours. |
| Current user lookup | `get_current_user()`. |

`get_current_user()` rejects:

- invalid or expired JWTs;
- JWT subjects that are not valid UUIDs;
- missing users;
- inactive users.

## Forced Password Change

CSV enrollment import can create new users with:

```text
hashed_password = ""
must_change_password = true
```

`get_current_app_user()` blocks normal app endpoints while `must_change_password` is true.

Allowed flow:

1. User logs in.
2. Frontend redirects to `/settings`.
3. User changes password through `/auth/change-password`.
4. Backend sets `must_change_password=false`.

## Roles

### Platform Role

Stored on `app_user.global_role`.

| Role | Meaning in backend services |
|---|---|
| `student` | Can use enrolled courses and own conversations. |
| `teacher` | Can create courses and manage courses where enrolled as teacher. |
| `admin` | Passes admin checks and course teacher checks. |

### Course Role

Stored on `course_enrollment.role`.

| Role | Meaning |
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

Conversation access is owner-based.

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
