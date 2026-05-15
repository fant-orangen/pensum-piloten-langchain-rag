# API Errors

Error helpers live in `src/api/utils/exception_util.py`.

FastAPI validation errors use FastAPI's default `422` response. Application errors use `HTTPException` with a `detail` field.

## Common Status Codes

| Status | Source | Meaning |
|---:|---|---|
| `400` | `bad_request_error()` | Invalid request state or unsupported input. |
| `401` | `unauthorized_error()` or auth dependency | Missing, invalid, or expired credentials. |
| `403` | `forbidden_error()` or dependency | Authenticated user lacks access or must change password. |
| `404` | `not_found_error()` | Requested row or accessible resource does not exist. |
| `409` | `conflict_error()` | Request conflicts with current state. |
| `413` | upload helpers | Upload exceeds configured size limits. |
| `422` | FastAPI/Pydantic | Path, query, body, or multipart validation failed. |
| `500` | `stage_error()` or unhandled server failure | Backend persistence, preparation, or chain setup failed. |
| `502` | `stage_error(status_code=502)` | Tutor chain failed to produce a response. |

## Error Shape

String detail:

```json
{
  "detail": "Course not found."
}
```

Stage-tagged detail:

```json
{
  "detail": "[message_agent_response_failed] Failed to obtain a response from the tutor agent."
}
```

## Auth Dependency Errors

`get_current_user()` returns `401` with:

```json
{
  "detail": "Invalid or expired credentials."
}
```

`get_current_app_user()` returns `403` with:

```json
{
  "detail": "Password change required before using this endpoint."
}
```

## Upload Errors

Upload size limit failures return `413`.

Unsupported direct upload file extensions return `400`.

Zip upload returns `400` when no supported files are extracted.

## Conversation Message Errors

`POST /conversations/{conversation_id}/messages` returns:

| Status | Detail |
|---:|---|
| `400` | `This course does not currently have ingested materials.` |
| `409` | `Course materials are currently being rebuilt.` |
| `400` | `[message_chain_configuration_invalid] ...` |
| `500` | `[message_chain_initialization_failed] ...` |
| `500` | `[message_history_compression_failed] ...` |
| `500` | `[message_history_load_failed] ...` |
| `502` | `[message_agent_response_failed] ...` |
| `500` | `[message_persistence_failed] ...` |

