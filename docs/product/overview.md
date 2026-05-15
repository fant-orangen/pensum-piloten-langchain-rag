# Product Overview

Pensum Piloten is a course-scoped RAG chat product.

Users start from the dashboard, open a course, and work inside that course's context. The course chat route is `/chat/:courseId`.

## Product Areas

| Area | Primary users | Purpose |
|---|---|---|
| Dashboard | Students, teachers | Entry point for enrolled courses and teacher-managed courses. |
| Course chat | Students, teachers using student view | Course-scoped conversations over indexed course material. |
| Course administration | Teachers | Manage students, materials, course instructions, teacher assignments, and course deletion. |
| User administration | Admins | Promote students to teachers and demote teachers to students. |
| Settings | Authenticated users | Password change and forced first-login password setup. |

## Documentation

| File | Scope |
|---|---|
| `roles.md` | Platform roles, course roles, and visible product areas. |
| `student-workflows.md` | Student dashboard, course chat, prompt modes, sources, settings. |
| `teacher-workflows.md` | Course creation, student management, materials, instructions, teacher assignment, course deletion. |
| `admin-workflows.md` | Admin user-management page behavior. |
| `prompt-modes.md` | Socratic, direct, and example prompt modes. |
