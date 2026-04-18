"""Tests for /conversations and /conversations/{id}/messages endpoints.

Run from the project root with the server already running:
    python tests/test_conversations.py

Requires SEED_TEST_DATA=true so the seeded experiment accounts and courses
exist. Does NOT send messages that invoke the RAG chain — for that see
test_conversation_flow.py.
"""

import sys
import os
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.http_client import RUN_ID, check, delete, get, login, post, section, summarise

STUDENT_EMAIL = "os_g1_student01@test.com"
STUDENT_PASSWORD = "password123"


def main() -> None:
    print(f"\nRun ID: {RUN_ID}")

    student_token = login(STUDENT_EMAIL, STUDENT_PASSWORD)

    # Resolve the seeded course the student is already enrolled in.
    _, courses = get("/courses", token=student_token, expected_status=200)
    if not courses:
        print("  No enrolled courses found. Is SEED_TEST_DATA=true and the server running?")
        sys.exit(1)
    seeded_course_id = courses[0]["id"]

    # ------------------------------------------------------------------
    section("POST /conversations")
    # ------------------------------------------------------------------

    code, body = post("/conversations", {"course_id": seeded_course_id}, token=student_token)
    check(code == 201, "Enrolled user creates conversation → 201")
    check(body is not None and "id" in body, "Response contains conversation id")
    conv_id = body["id"] if body else None

    code, _ = post("/conversations", {"course_id": seeded_course_id})
    check(code == 401, "Unauthenticated → 401")

    code, _ = post("/conversations", {"course_id": str(uuid.uuid4())}, token=student_token)
    check(code in (403, 404), "Not-enrolled course → 403 or 404")

    # ------------------------------------------------------------------
    section("GET /conversations")
    # ------------------------------------------------------------------

    code, body = get("/conversations", token=student_token)
    check(code == 200, "Authenticated → 200")
    check(body is not None and "items" in body, "Response is paginated")
    check(body is not None and "total" in body, "Response includes total count")

    ids_in_page = [c["id"] for c in body["items"]] if body else []
    check(conv_id in ids_in_page, "Newly created conversation appears in list")

    code, _ = get("/conversations")
    check(code == 401, "Unauthenticated → 401")

    # ------------------------------------------------------------------
    section("GET /conversations/{id}/messages")
    # ------------------------------------------------------------------

    code, body = get(f"/conversations/{conv_id}/messages", token=student_token)
    check(code == 200, "Owner retrieves messages → 200")
    check(body is not None and "items" in body, "Response is paginated")

    # A different user must not access another user's conversation.
    other_email = f"other_{RUN_ID}@example.com"
    post("/auth/register", {
        "email": other_email,
        "password": "password123",
        "first_name": "Other",
        "last_name": "User",
    }, expected_status=201)
    other_token = login(other_email, "password123")

    code, _ = get(f"/conversations/{conv_id}/messages", token=other_token)
    check(code == 403, "Non-owner retrieves messages → 403")

    code, _ = get(f"/conversations/{str(uuid.uuid4())}/messages", token=student_token)
    check(code == 404, "Nonexistent conversation → 404")

    code, _ = get(f"/conversations/{conv_id}/messages")
    check(code == 401, "Unauthenticated → 401")

    # ------------------------------------------------------------------
    section("DELETE /conversations/{id}")
    # ------------------------------------------------------------------

    code, _ = delete(f"/conversations/{conv_id}", token=other_token)
    check(code == 403, "Non-owner deletes conversation → 403")

    code, _ = delete(f"/conversations/{str(uuid.uuid4())}", token=student_token)
    check(code == 404, "Delete nonexistent conversation → 404")

    code, _ = delete(f"/conversations/{conv_id}")
    check(code == 401, "Unauthenticated delete → 401")

    code, body = delete(f"/conversations/{conv_id}", token=student_token)
    check(code == 204, "Owner deletes conversation → 204")
    check(body is None, "Delete returns empty body")

    code, _ = get(f"/conversations/{conv_id}/messages", token=student_token)
    check(code == 404, "Deleted conversation messages no longer accessible → 404")

    code, body = get("/conversations", token=student_token)
    ids_in_page = [c["id"] for c in body["items"]] if body else []
    check(conv_id not in ids_in_page, "Deleted conversation no longer appears in list")

    summarise()


if __name__ == "__main__":
    main()
