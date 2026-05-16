# Auth API

Router: `src/api/routers/auth.py`

Schemas: `src/api/schemas/auth.py`

## Endpoints

| Method | Path | Auth | Response |
|---|---|---|---|
| `POST` | `/auth/register` | No | `UserResponse` |
| `POST` | `/auth/login` | No | `TokenResponse` |
| `GET` | `/auth/me` | Bearer token | `UserResponse` |
| `POST` | `/auth/change-password` | Bearer token | `204 No Content` |

## `POST /auth/register`

Creates a student account.

Request:

```json
{
  "email": "student@example.com",
  "password": "password123",
  "first_name": "Ada",
  "last_name": "Lovelace"
}
```

Validation:

- `email` must be a valid email address;
- `password` minimum length is `8`;
- `first_name` minimum length is `1`;
- `last_name` minimum length is `1`.

Behavior:

- stores a bcrypt password hash;
- returns the created user without `hashed_password`;
- returns `409` if the email already exists.

## `POST /auth/login`

Exchanges credentials for a JWT access token.

Request:

```json
{
  "email": "student@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Behavior:

- returns `401` for unknown email or wrong password;
- allows `must_change_password=true` users through so they can call `/auth/change-password`.

## `GET /auth/me`

Returns the authenticated user profile.

Response fields:

| Field | Type |
|---|---|
| `id` | UUID |
| `email` | string |
| `first_name` | string |
| `last_name` | string |
| `global_role` | string |
| `system_prompt_mode` | integer |
| `must_change_password` | boolean |

This endpoint uses `get_current_user()`, not `get_current_app_user()`. It is available to forced-password-change users.

## `POST /auth/change-password`

Changes the authenticated user's password.

Request:

```json
{
  "old_password": "old-password",
  "new_password": "new-password"
}
```

Validation:

- `new_password` minimum length is `8`;
- `old_password` is required for normal users;
- `old_password` is not verified when `must_change_password=true`.

Behavior:

- stores a new bcrypt hash;
- sets `must_change_password=false`;
- returns `400` when a normal user's old password is missing or incorrect.

