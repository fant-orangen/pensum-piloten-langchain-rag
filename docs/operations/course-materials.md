# Course Materials Operations

Course materials are managed by `src/api/services/course_documents.py` and exposed through `src/api/routers/courses.py`.

## Storage

Course documents live under the course's `documents_dir`.

Course directories are built from:

```text
DOCUMENTS_DIR/<COURSE_CODE>
```

Rebuild artifacts are written under:

```text
<course documents dir>/.pensum_piloten/
```

Artifact files:

| File | Contents |
|---|---|
| `kg_triplets.json` | Extracted KG triplets for the rebuilt scope. |
| `rebuild_manifest.json` | Course id, course code, scope, index version, document list, chunk count, triplet count, rebuild timestamp. |

## Supported Files

The loader accepts these extensions:

```text
.pdf, .docx, .html, .htm,
.txt, .md, .rst, .csv, .tsv, .json, .jsonl, .yaml, .yml, .xml,
.sql, .py, .java, .js, .ts, .tsx, .jsx, .c, .h, .cpp, .hpp,
.go, .rs, .kt, .swift, .php, .rb, .sh, .css, .scss, .sass,
.ini, .cfg, .conf, .toml, .log
```

Unsupported files are rejected for direct uploads. Unsupported files inside zip archives are reported in the skipped list.

## Staged Changes

Document statuses:

| Status | Meaning |
|---|---|
| `active` | Included in the current active course scope. |
| `pending_add` | Uploaded and waiting for confirm/rebuild. |
| `pending_remove` | Active document staged for removal from the next scope. |

Endpoints:

| Endpoint | Operation |
|---|---|
| `GET /courses/{course_id}/documents` | List active and staged documents. |
| `POST /courses/{course_id}/documents` | Stage uploaded files as `pending_add`. |
| `POST /courses/{course_id}/documents/zip` | Extract supported zip members and stage them as `pending_add`. |
| `DELETE /courses/{course_id}/documents/{document_id}` | Delete `pending_add` immediately or mark `active` as `pending_remove`. |
| `DELETE /courses/{course_id}/documents` | Stage all active documents for removal and delete pending additions. |
| `GET /courses/{course_id}/documents/status` | Return rebuild status, active scope, index version, and pending counts. |
| `POST /courses/{course_id}/documents/confirm` | Queue a rebuild and start the background rebuild task. |

All course material endpoints require course teacher or admin access.

## Rebuild Lifecycle

Course rebuild statuses:

| Status | Meaning |
|---|---|
| `idle` | No rebuild is queued or running. |
| `queued` | Staged changes were confirmed and the background task has been scheduled. |
| `building` | Rebuild task is loading, chunking, embedding, and building retrieval stores. |
| `failed` | Rebuild failed; `course.rebuild_error` stores the truncated error message. |

Rebuild sequence:

1. Set `course.rebuild_status` to `building`.
2. Build the next scope name as `<COURSE_CODE>_v<index_version + 1>`.
3. Load active and `pending_add` documents, excluding `pending_remove`.
4. Chunk documents and assign chunk IDs.
5. Build the Chroma collection for the target scope.
6. For `kg_rag`, extract triplets and build the Neo4j scope.
7. Write `.pensum_piloten` artifacts.
8. Promote `pending_add` to `active` and delete `pending_remove` rows.
9. Set `course.chroma_collection` to the new scope and `course.index_version` to the new version.
10. Set `course.rebuild_status` to `idle`.
11. Delete removed files and clear the old Chroma/Neo4j scope.

If the snapshot contains no documents, the rebuild clears the active scope and sets `course.chroma_collection` to `null`.

## Failure Handling

If rebuild fails before activation:

- the target Chroma/Neo4j scope is deleted;
- staged document statuses stay unchanged;
- `course.rebuild_status` becomes `failed`;
- `course.rebuild_error` stores the error message truncated to 1000 characters.

Cleanup failures after activation are logged and do not roll back the activated scope.
