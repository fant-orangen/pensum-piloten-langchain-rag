# Roles

Pensum Piloten uses platform roles and course enrollment roles.

## Platform Roles

| Role | Product behavior |
|---|---|
| `student` | Sees enrolled courses on the dashboard and can chat in those courses. |
| `teacher` | Can create courses, manage courses where enrolled as teacher, and chat in courses where enrolled as student. |
| `admin` | Frontend redirects to `/dashboard/admin` for user role management. Backend admin checks also pass course teacher and owner checks. |

## Course Roles

| Course role | Product behavior |
|---|---|
| `student` | Can open the course chat and create conversations. |
| `teacher` | Can open the course administration page for that course. |

Course role is separate from platform role. A platform teacher can be a student in one course and a teacher in another.

## Frontend Entry Points

| User state | Route |
|---|---|
| Not authenticated | `/login` |
| Authenticated student | `/` |
| Authenticated teacher | `/` |
| Authenticated admin | `/dashboard/admin` |
| Must change password | `/settings` |

## Course Access

| Action | Required product access |
|---|---|
| Open course chat | Course enrollment or admin access on the backend. |
| Create course | Platform `teacher` or `admin`. |
| Manage students | Course teacher or admin. |
| Manage materials | Course teacher or admin. |
| Edit course instructions | Course teacher or admin. |
| Manage course teachers | Course creator or admin. |
| Delete course | Course creator or admin. |
