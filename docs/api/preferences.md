# Preferences API

Router: `src/api/routers/preferences.py`

Schemas: `src/api/schemas/preferences.py`

All endpoints require `get_current_app_user()`.

## Endpoints

| Method | Path | Response |
|---|---|---|
| `PATCH` | `/preferences/system-prompt` | `SystemPromptPreferenceUpdateResponse` |

## `PATCH /preferences/system-prompt`

Updates the authenticated user's default prompt mode for new conversations.

Request:

```json
{
  "mode": 2
}
```

Supported values:

| Value | Mode |
|---:|---|
| `1` | Socratic |
| `2` | Direct |
| `3` | Example |

Response:

```json
{
  "success": true,
  "message": "System prompt mode updated successfully.",
  "mode": 2
}
```

Behavior:

- persists the mode on `app_user.system_prompt_mode`;
- does not update existing conversations;
- new conversations copy the user's current mode into `conversation.system_prompt_mode`.

