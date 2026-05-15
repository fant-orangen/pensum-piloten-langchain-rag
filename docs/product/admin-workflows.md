# Admin Workflows

The admin page route is:

```text
/dashboard/admin
```

Frontend route behavior:

- authenticated admins are redirected to `/dashboard/admin`;
- the page lists student and teacher users;
- search filters by first name, last name, and email.

## Role Management

Admin page actions:

| Action | Effect |
|---|---|
| Promote selected students | Sets selected users to platform role `teacher`. |
| Demote selected teachers | Sets selected users to platform role `student`. |

Teachers who own courses are disabled in the demotion list.

The backend also rejects demotion of a teacher who created a course.

## Data Source

The admin page uses:

| Frontend function | Backend route |
|---|---|
| `getAdminUsers()` | `GET /admin/users` |
| `promoteToTeacher(userId)` | `POST /admin/users/{user_id}/promote` |
| `demoteToStudent(userId)` | `POST /admin/users/{user_id}/demote` |

Admin user-management restrictions are documented in `docs/security/authentication.md`.
