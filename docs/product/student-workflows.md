# Student Workflows

## Dashboard

Students land on the dashboard after login.

Dashboard behavior:

- shows courses returned by `GET /courses`;
- opens a course chat at `/chat/:courseId`;
- shows an empty state when the student has no enrolled courses.

## Course Chat

The course chat page is scoped to one course.

Main chat capabilities:

| Capability | Behavior |
|---|---|
| Course header | Loads safe course metadata from `GET /courses/{course_id}`. |
| Conversation list | Loads the user's conversations filtered by course. |
| New conversation | Creates a conversation for the selected course. |
| Rename conversation | Updates the selected conversation title. |
| Delete conversation | Removes the selected conversation. |
| Send message | Sends a human message and displays the generated assistant response. |
| Sources | Opens source chunks attached to an AI message. |
| Prompt mode | Updates the user's prompt-mode preference. |

## Material Availability

When the course has no active material index, message sending fails with:

```text
This course does not currently have ingested materials.
```

When course materials are queued or building, message sending fails with:

```text
Course materials are currently being rebuilt.
```

The frontend displays Norwegian error toasts for both states.

## Message Sources

AI responses can include source references. The source panel resolves stored chunk IDs through:

```text
GET /conversations/{conversation_id}/messages/{message_id}/sources
```

The source panel is available only for messages with resolvable source chunks.

## Settings

Users can change password from `/settings`.

Imported users with `must_change_password=true` are redirected to `/settings` and cannot use normal app pages until they set a password.
