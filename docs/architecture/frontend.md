# Frontend Architecture

The frontend is a React single-page app built with Vite and TypeScript.

Source files:

- Route tree: `frontend/src/App.tsx`
- Auth context: `frontend/src/contexts/AuthContext.tsx`
- API client: `frontend/src/api/client.ts`
- API modules: `frontend/src/api/`
- Shared types: `frontend/src/types/index.ts`
- Pages: `frontend/src/pages/`

## Providers

`App.tsx` wraps the app with:

| Provider | Purpose |
|---|---|
| `QueryClientProvider` | TanStack Query server state. |
| `BrowserRouter` | React Router routes. |
| `AuthProvider` | JWT and current user state. |
| `Toaster` | Toast notifications. |

TanStack Query defaults:

- `staleTime`: 30 seconds;
- `retry`: 1.

## Routes

| Route | Component | Guard |
|---|---|---|
| `/login` | `AuthPage` | Public. |
| `/` | `DashboardPage` | Authenticated. |
| `/chat` | `ChatPage` | Authenticated. |
| `/chat/:courseId` | `ChatPage` | Authenticated. |
| `/manage/:courseId` | `TeacherCoursePage` | Requires platform role `teacher` or higher in frontend guard. |
| `/dashboard/admin` | `AdminPage` | Requires platform role `admin`. |
| `/settings` | `SettingsPage` | Authenticated. |
| `*` | Redirect to `/` | Fallback. |

`ProtectedRoute` also redirects forced-password-change users to `/settings`.

## API Client

`apiClient` is a shared Axios instance.

| Behavior | Implementation |
|---|---|
| Base URL | `import.meta.env.VITE_API_BASE_URL ?? ""`. |
| Auth header | Request interceptor reads `access_token` from `localStorage`. |
| 401 handling | Response interceptor clears `access_token` and redirects to `/login`, except for login requests. |

API modules map directly to backend router groups:

| Module | Backend group |
|---|---|
| `auth.ts` | `/auth` |
| `courses.ts` | `/courses` |
| `conversations.ts` | `/conversations` |
| `preferences.ts` | `/preferences` |
| `admin.ts` | `/admin` |

## Authentication State

`AuthProvider` stores:

- `user`;
- `token`;
- `isLoading`.

Session restore:

1. On mount, read `access_token` from `localStorage`.
2. If present, call `GET /auth/me`.
3. If the request fails, clear local auth state and remove `access_token`.

Login:

1. Call `POST /auth/login`.
2. Store returned token in `localStorage`.
3. Call `GET /auth/me`.
4. Store the returned user profile.

Register:

1. Call `POST /auth/register`.
2. Call login with the same credentials.

Logout removes `access_token` and clears `user`.

## Dashboard

`DashboardPage` chooses course queries based on platform role.

| User role | Queries | UI path |
|---|---|---|
| `student` | `getCourses()` | Shows enrolled courses. |
| `teacher` | `getResponsibleCourses()`, `getAvailableCourses()` | Shows managed courses and available student courses. |
| `admin` | Same branch as teacher in `DashboardPage`, but `ProtectedRoute` redirects admins to `/dashboard/admin`. |

Teachers can open the create-course modal from the dashboard.

## Chat Page

`ChatPage` coordinates:

- selected course;
- conversation list;
- selected conversation;
- message pagination;
- optimistic pending human message;
- prompt mode selection;
- source panel state.

Main backend calls:

| Action | API function |
|---|---|
| Load course summary | `getCourse(courseId)` |
| List conversations | `getConversations(page, pageSize, courseId)` |
| Create conversation | `createConversation(courseId)` |
| List messages | `getMessages(conversationId, page, pageSize)` |
| Send message | `sendMessage(conversationId, content)` |
| Rename conversation | `renameConversation(conversationId, title)` |
| Delete conversation | `deleteConversation(conversationId)` |
| Update prompt mode | `updateSystemPromptMode(mode)` |
| Resolve sources | `getMessageSources(conversationId, messageId)` |

The page handles two backend error details specially:

| Backend detail | UI message |
|---|---|
| `This course does not currently have ingested materials.` | Course has no sources. |
| `Course materials are currently being rebuilt.` | Course materials are processing. |

## Teacher Course Page

`TeacherCoursePage` contains tabs for course administration.

| Tab | Component | Availability |
|---|---|---|
| Students | `StudentsTab` | Course teacher page. |
| Materials | `MaterialsTab` | Course teacher page. |
| Instructions | `InstructionsTab` | Course teacher page. |
| Teachers | `TeachersTab` | Course creator only. |
| Admin | `AdminTab` | Course creator or platform admin. |

The page gets courses from `getResponsibleCourses()` and finds the active course by route `courseId`.

## Materials Tab

`MaterialsTab` handles source document lifecycle.

| UI action | API call |
|---|---|
| List documents | `getCourseDocuments(courseId)` |
| Upload regular files | `uploadDocuments(courseId, files)` |
| Upload zip | `uploadZip(courseId, file)` |
| Delete one document | `deleteDocument(courseId, documentId)` |
| Delete all documents | `deleteAllDocuments(courseId)` |
| Read rebuild status | `getDocumentsStatus(courseId)` |
| Confirm ingestion | `confirmIngestion(courseId)` |

`getDocumentsStatus()` is polled every 3 seconds while status is `queued` or `building`.

## Students Tab

`StudentsTab` handles student enrollment management for a course.

| UI action | API call |
|---|---|
| List students | `getCourseStudents(courseId, page, pageSize, search)` |
| Enroll one existing user by email | `enrollStudent(courseId, email)` |
| Remove one student | `unenrollStudent(courseId, userId)` |
| Preview CSV import | `previewEnrollmentImport(courseId, file)` |
| Confirm CSV import | `confirmEnrollmentImport(courseId, previewId)` |
| Cancel CSV import | `cancelEnrollmentImport(courseId, previewId)` |

The students list uses infinite pagination with page size `20`. The search field is sent to the backend and matches student name or email.

CSV import is a two-step backend workflow:

1. Preview parses the CSV and stores an `enrollment_import_preview` row.
2. Confirm re-classifies candidates, creates missing user accounts with `must_change_password=true`, creates enrollments, and deletes the preview row.

Cancel deletes the preview row without changing enrollments.

## Query Keys

Query keys are grouped near their pages:

- `frontend/src/pages/dashboard/queryKeys.ts`
- `frontend/src/pages/chat/queryKeys.ts`
- `frontend/src/pages/teacher-course/queryKeys.ts`

Mutations invalidate the relevant query groups after successful changes.

## Shared Types

Frontend API types are defined in `frontend/src/types/index.ts`.

Important shared unions:

| Type | Values |
|---|---|
| `GlobalRole` | `student`, `teacher`, `admin` |
| `SystemPromptMode` | `1`, `2`, `3` |
| `DocumentStatus` | `pending_add`, `active`, `pending_remove` |
| `RebuildStatus` | `idle`, `queued`, `building`, `failed` |
| `MessageRole` | `human`, `ai` |
| `RagMode` | `kg_rag`, `naive_rag` |
