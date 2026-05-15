# Frontend Development

Frontend code lives under `frontend/src/`.

## Structure


| Path                       | Role                                                 |
| -------------------------- | ---------------------------------------------------- |
| `App.tsx`                  | Provider composition and route tree.                 |
| `api/`                     | Typed API client functions around `apiClient`.       |
| `components/`              | Shared UI components.                                |
| `contexts/AuthContext.tsx` | Authentication state and auth actions.               |
| `hooks/`                   | Shared React hooks.                                  |
| `pages/`                   | Route-level page components.                         |
| `types/index.ts`           | Frontend TypeScript models matching backend schemas. |


## Runtime State


| State                        | Implementation                                   |
| ---------------------------- | ------------------------------------------------ |
| Authenticated user and token | `AuthContext`                                    |
| JWT persistence              | `localStorage` key `access_token`                |
| Server state                 | TanStack Query                                   |
| API transport                | Axios `apiClient`                                |
| Prompt mode preference       | `/preferences` API and frontend preference types |


`apiClient` attaches the bearer token on requests. A non-login `401` response clears `access_token` and redirects to `/login`.

## Routing

Routes are defined in `frontend/src/App.tsx`.


| Route               | Component           | Guard         |
| ------------------- | ------------------- | ------------- |
| `/login`            | `AuthPage`          | none          |
| `/`                 | `DashboardPage`     | authenticated |
| `/chat/:courseId`   | `ChatPage`          | authenticated |
| `/manage/:courseId` | `TeacherCoursePage` | teacher       |
| `/dashboard/admin`  | `AdminPage`         | admin         |
| `/settings`         | `SettingsPage`      | authenticated |

The chat route requires `courseId`; `/chat` falls through to the fallback redirect.


`ProtectedRoute` applies frontend navigation rules. Backend authorization remains the security boundary.

## API Clients

Each backend route group has a matching frontend API module:


| Backend group    | Frontend module                     |
| ---------------- | ----------------------------------- |
| `/auth`          | `frontend/src/api/auth.ts`          |
| `/courses`       | `frontend/src/api/courses.ts`       |
| `/conversations` | `frontend/src/api/conversations.ts` |
| `/preferences`   | `frontend/src/api/preferences.ts`   |
| `/admin`         | `frontend/src/api/admin.ts`         |


API functions return typed response bodies from `frontend/src/types/index.ts`.

## Build Settings


| File                          | Setting                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------- |
| `frontend/tsconfig.json`      | `strict`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`. |
| `frontend/vite.config.ts`     | Dev proxy for backend route prefixes to `http://localhost:8000`.                |
| `frontend/tailwind.config.js` | Tailwind content paths and `primary` color scale.                               |


Build command:

```bash
npm run build
```
