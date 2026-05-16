# Logging and Errors

Backend services use shared helpers for HTTP errors and structured logs.

## HTTP Errors

Error helpers live in `src/api/utils/exception_util.py`.

| Helper | Status |
|---|---|
| `bad_request_error()` | `400` |
| `unauthorized_error()` | `401` |
| `forbidden_error()` | `403` |
| `not_found_error()` | `404` |
| `conflict_error()` | `409` |
| `stage_error()` | caller-provided status, default `500` |

Use these helpers in services instead of constructing repeated `HTTPException` objects.

`stage_error(code, message, status_code=...)` returns a string detail in this format:

```text
[code] Message.
```

The message service uses stage-tagged errors for chain setup, history preparation, persistence, and agent response failures.

## Structured Logs

Logging helpers live in `src/api/utils/logging_util.py`.

| Helper | Use |
|---|---|
| `get_service_logger(module_name)` | Create a service logger with `component="api_service"` and service name. |
| `bind_log_context(logger, **fields)` | Bind normalized context such as UUIDs and paths. |
| `log_chain_invocation()` | Emit the standard message-chain invocation event. |
| `log_course_material_rebuild()` | Emit high-level course material rebuild lifecycle events. |
| `log_course_material_rebuild_step()` | Emit rebuild step events. |
| `log_course_material_rebuild_failed()` | Emit rebuild failure events. |
| `log_conversation_compression()` | Emit conversation compression lifecycle events. |

The normalizer converts UUIDs, paths, mappings, and sequences to log-friendly primitive values.

## Event Naming

Course material rebuild logs use these event families:

| Event family | Examples |
|---|---|
| Lifecycle | `course_material_rebuild_queued`, `course_material_rebuild_started`, `course_material_rebuild_complete` |
| Step | `course_material_rebuild_step` with a `step` field |
| Failure | `course_material_rebuild_failed` |
| Missing target | `course_material_rebuild_missing_course` |

Conversation compression logs use:

- `conversation_compression_triggered`
- `conversation_compression_completed`
