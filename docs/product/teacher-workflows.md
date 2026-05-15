# Teacher Workflows

Teachers use the dashboard and course administration pages.

## Dashboard

Teacher dashboard sections:

| Section | Source | Destination |
|---|---|---|
| Mine emner | `GET /courses/responsible` | `/manage/:courseId` |
| Tilgjengelige emner | `GET /courses/available` | `/chat/:courseId` |

Teachers can create a course from the dashboard. Course creation enrolls the creating user as a course teacher.

## Course Administration

Course administration route:

```text
/manage/:courseId
```

Tabs visible to course teachers:

| Tab | Purpose |
|---|---|
| Studenter | Student list, single-student enrollment, CSV enrollment import, student removal. |
| Læringsmateriell | Document upload, zip upload, staged removal, rebuild status, rebuild confirmation. |
| Instruksjoner | Course-specific instructions injected into tutor prompts. |

Tabs visible to the course creator:

| Tab | Purpose |
|---|---|
| Lærere | Add and remove course teachers. The creator cannot be removed. |
| Admin | Delete the course. |

Platform admins pass the backend owner checks. The frontend route guard sends admins to `/dashboard/admin`.

## Student Management

Student tab capabilities:

- list enrolled students with search and pagination;
- enroll an existing user by email;
- preview a CSV import before changes are applied;
- create missing student accounts during confirmed CSV import;
- remove students with confirmation.

CSV import accepts rows with:

```text
email, first_name, last_name
```

Name columns are optional. Header detection accepts known email header labels.

## Material Management

Material tab capabilities:

- upload files;
- upload one zip archive;
- stage active documents for removal;
- delete pending additions immediately;
- stage all active documents for removal;
- view rebuild status, index version, pending additions, pending removals, and rebuild error;
- confirm staged changes to start the rebuild.

Staged changes become active only after the rebuild succeeds.

## Course Instructions

Teachers can edit course-specific instructions.

Product behavior:

- maximum length in the frontend is 3000 characters;
- blank text clears the stored instructions;
- saved instructions are included in tutor prompts for the course.

## Teacher Assignment

The course creator can:

- view global teachers who are not assigned to the course;
- add selected teachers to the course;
- view teachers already assigned to the course;
- remove selected course teachers.

The course creator is shown in the course teacher list and cannot be selected for removal.

## Course Deletion

The course creator can delete the course from the Admin tab.

Course deletion removes:

- the course;
- enrollments;
- conversations and messages;
- course document rows and files;
- active Chroma and Neo4j course scopes.

Deletion is blocked while course materials are queued or building.
