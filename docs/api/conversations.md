# Conversations API

Router: `src/api/routers/conversations.py`

Schemas:

- `src/api/schemas/conversation.py`
- `src/api/schemas/message.py`
- `src/api/schemas/pagination.py`

All endpoints require `get_current_app_user()`. Forced-password-change users receive `403`.

## Endpoints

| Method | Path | Response |
|---|---|---|
| `GET` | `/conversations` | `Page[ConversationRead]` |
| `POST` | `/conversations` | `ConversationRead` |
| `GET` | `/conversations/{conversation_id}/messages` | `Page[MessageRead]` |
| `POST` | `/conversations/{conversation_id}/messages` | `MessageRead` |
| `GET` | `/conversations/{conversation_id}/messages/{message_id}/sources` | `list[MessageSourceRead]` |
| `PATCH` | `/conversations/{conversation_id}` | `ConversationRead` |
| `DELETE` | `/conversations/{conversation_id}` | `204 No Content` |

## Access Rules

| Operation | Access rule |
|---|---|
| List conversations | Returns only current user's conversations. |
| Create conversation | User must be enrolled in the course. |
| Read messages | Conversation must belong to current user. |
| Send message | Conversation must belong to current user. |
| Read sources | Conversation must belong to current user. |
| Rename | Conversation must belong to current user. |
| Delete | Conversation must belong to current user. |

## `GET /conversations`

Query parameters:

| Parameter | Type | Constraint |
|---|---|---|
| `page` | integer | default `1`, minimum `1` |
| `page_size` | integer | default `20`, range `1..100` |
| `course_id` | UUID | optional |

Ordering: `updated_at` descending.

## `POST /conversations`

Request:

```json
{
  "course_id": "00000000-0000-0000-0000-000000000000"
}
```

Behavior:

- copies `current_user.system_prompt_mode` to `conversation.system_prompt_mode`;
- returns `403` when the user is not enrolled in the course;
- returns `404` when the course does not exist.

## `GET /conversations/{conversation_id}/messages`

Query parameters:

| Parameter | Type | Constraint |
|---|---|---|
| `page` | integer | default `1`, minimum `1` |
| `page_size` | integer | default `50`, range `1..100` |

Ordering: newest first by `created_at` descending.

## `POST /conversations/{conversation_id}/messages`

Request:

```json
{
  "content": "Explain paging."
}
```

Validation:

- `content` minimum length is `1`;
- `content` maximum length is `10000`.

Behavior:

- persists the human message and generated AI response in one service flow;
- returns the AI message;
- returns `400` if the course has no active material index;
- returns `409` if course materials are `queued` or `building`;
- returns `502` if the tutor chain fails to produce a response.

`MessageRead.conversation_compression_triggered` indicates whether conversation compression ran during the request.

## `GET /conversations/{conversation_id}/messages/{message_id}/sources`

Returns resolved source chunks for an AI message.

Response item:

| Field | Meaning |
|---|---|
| `chunk_id` | Chroma chunk identifier. |
| `document` | Source document name. |
| `page` | Source page string. |
| `content` | Chunk text resolved from Chroma. |

## `PATCH /conversations/{conversation_id}`

Request:

```json
{
  "title": "Paging notes"
}
```

Validation:

- `title` minimum length is `1`;
- `title` maximum length is `200`.

## `DELETE /conversations/{conversation_id}`

Deletes the conversation owned by the current user. PostgreSQL cascades dependent messages and conversation context summary rows.

