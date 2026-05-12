"""Tests for /courses and /courses/{id}/enrollments endpoints.

Run from the project root with the server already running:
    python tests/test_courses.py

Requires SEED_TEST_DATA=true so the seeded teacher and student accounts exist.
"""

import sys
import os
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.http_client import RUN_ID, check, delete, get, login, post, post_multipart, section, summarise

TEACHER_EMAIL = "teacher@test.com"
TEACHER_PASSWORD = "password123"
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "password123"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "password123"


def main() -> None:
    print(f"\nRun ID: {RUN_ID}")

    teacher_token = login(TEACHER_EMAIL, TEACHER_PASSWORD)
    student_token = login(STUDENT_EMAIL, STUDENT_PASSWORD)
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)

    # ------------------------------------------------------------------
    section("GET /courses")
    # ------------------------------------------------------------------

    code, body = get("/courses", token=student_token)
    check(code == 200, "Authenticated → 200")
    check(isinstance(body, list) and len(body) > 0, "Student sees seeded enrolled course")

    code, _ = get("/courses")
    check(code == 401, "Unauthenticated → 401")

    # ------------------------------------------------------------------
    section("GET /courses/available")
    # ------------------------------------------------------------------

    code, body = get("/courses/available", token=student_token)
    check(code == 200, "Student: /courses/available → 200")
    check(isinstance(body, list) and len(body) > 0, "Student sees seeded enrolled course in /courses/available")

    code, body = get("/courses/available", token=teacher_token)
    check(code == 200, "Teacher: /courses/available → 200")
    check(isinstance(body, list) and len(body) == 0, "Teacher sees no student-role courses in /courses/available")

    code, _ = get("/courses/available")
    check(code == 401, "Unauthenticated /courses/available → 401")

    # ------------------------------------------------------------------
    section("GET /courses/responsible")
    # ------------------------------------------------------------------

    code, body = get("/courses/responsible", token=teacher_token)
    check(code == 200, "Teacher: /courses/responsible → 200")
    check(isinstance(body, list) and len(body) > 0, "Teacher sees seeded teacher-role course in /courses/responsible")

    code, body = get("/courses/responsible", token=student_token)
    check(code == 200, "Student: /courses/responsible → 200")
    check(isinstance(body, list) and len(body) == 0, "Student sees no courses in /courses/responsible")

    code, _ = get("/courses/responsible")
    check(code == 401, "Unauthenticated /courses/responsible → 401")

    # ------------------------------------------------------------------
    section("POST /courses")
    # ------------------------------------------------------------------

    course_code = f"TST{RUN_ID}"
    code, body = post("/courses", {
        "name": f"Test Course {RUN_ID}",
        "code": course_code,
        "chroma_collection": f"test_col_{RUN_ID}",
        "documents_dir": f"docs/test_{RUN_ID}",
    }, token=teacher_token)
    check(code == 201, "Teacher creates course → 201")
    check(body is not None and body.get("code") == course_code, "Response contains correct course code")
    course = body

    second_course_code = f"TSB{RUN_ID}"
    code, body = post("/courses", {
        "name": f"Second Test Course {RUN_ID}",
        "code": second_course_code,
        "chroma_collection": f"test_col_second_{RUN_ID}",
        "documents_dir": f"docs/test_second_{RUN_ID}",
    }, token=teacher_token)
    check(code == 201, "Teacher creates second course → 201")
    check(body is not None and body.get("code") == second_course_code, "Second course response contains correct code")
    second_course = body

    code, _ = post("/courses", {
        "name": "Forbidden",
        "code": f"FRB{RUN_ID}",
        "chroma_collection": f"forbidden_{RUN_ID}",
        "documents_dir": "docs/forbidden",
    }, token=student_token)
    check(code == 403, "Student creates course → 403")

    code, _ = post("/courses", {
        "name": "Duplicate",
        "code": course_code,
        "chroma_collection": f"dup_{RUN_ID}",
        "documents_dir": "docs/dup",
    }, token=teacher_token)
    check(code == 409, "Duplicate course code → 409")

    course_id = course["id"]
    second_course_id = second_course["id"]

    # ------------------------------------------------------------------
    section("POST/GET/DELETE /courses/{course_id}/documents")
    # ------------------------------------------------------------------

    document_content = b"Course notes for integration test."
    code, body = post_multipart(
        f"/courses/{course_id}/documents",
        files=[("files", "notes.txt", document_content, "text/plain")],
        token=teacher_token,
    )
    check(code == 201, "Teacher uploads document → 201")
    check(
        isinstance(body, list)
        and len(body) == 1
        and body[0].get("original_filename") == "notes.txt",
        "Upload returns document metadata",
    )
    document_id = body[0]["id"] if isinstance(body, list) and body else None

    code, body = get(f"/courses/{course_id}/documents", token=teacher_token)
    check(code == 200, "Teacher lists documents → 200")
    check(
        isinstance(body, list) and any(item.get("id") == document_id for item in body),
        "Uploaded document appears in teacher listing",
    )

    code, body = get(f"/courses/{course_id}/documents", token=admin_token)
    check(code == 200, "Admin lists documents → 200")
    check(isinstance(body, list), "Admin receives document list")

    code, _ = post_multipart(
        f"/courses/{course_id}/documents",
        files=[("files", "blocked.txt", b"forbidden", "text/plain")],
        token=student_token,
    )
    check(code == 403, "Student uploads document → 403")

    code, _ = get(f"/courses/{course_id}/documents", token=student_token)
    check(code == 403, "Student lists documents → 403")

    code, _ = delete(f"/courses/{course_id}/documents/{document_id}", token=student_token)
    check(code == 403, "Student deletes document → 403")

    code, _ = delete(f"/courses/{course_id}/documents/{document_id}", token=teacher_token)
    check(code == 204, "Teacher deletes pending-add document → 204")

    code, _ = delete(f"/courses/{course_id}/documents/{document_id}", token=teacher_token)
    check(code == 404, "Delete already-deleted document → 404")

    code, _ = get(f"/courses/{str(uuid.uuid4())}/documents", token=teacher_token)
    check(code == 404, "List documents for nonexistent course → 404")

    code, _ = post_multipart(
        f"/courses/{str(uuid.uuid4())}/documents",
        files=[("files", "missing-course.txt", b"x", "text/plain")],
        token=teacher_token,
    )
    check(code == 404, "Upload document to nonexistent course → 404")

    code, _ = post_multipart(
        f"/courses/{course_id}/documents",
        files=[("files", "unsupported.exe", b"not a document", "application/octet-stream")],
        token=teacher_token,
    )
    check(code == 400, "Upload unsupported document type → 400")

    code, _ = get(f"/courses/{course_id}/documents")
    check(code == 401, "Unauthenticated list documents → 401")

    # ------------------------------------------------------------------
    section("GET/POST /courses/{course_id}/documents/status and confirm")
    # ------------------------------------------------------------------

    code, body = get(f"/courses/{course_id}/documents/status", token=teacher_token)
    check(code == 200, "Teacher gets document status → 200")
    check(
        isinstance(body, dict)
        and "pending_additions" in body
        and "pending_removals" in body,
        "Document status includes pending counts",
    )

    code, _ = get(f"/courses/{course_id}/documents/status", token=student_token)
    check(code == 403, "Student gets document status → 403")

    code, _ = post(f"/courses/{second_course_id}/documents/confirm", token=teacher_token)
    check(code == 400, "Confirm with no staged document changes → 400")

    code, _ = get(f"/courses/{course_id}/documents/status")
    check(code == 401, "Unauthenticated document status → 401")

    # ------------------------------------------------------------------
    section("POST /courses/{course_id}/enrollments")
    # ------------------------------------------------------------------

    # Register a fresh user as enrollment target.
    enroll_email = f"enroll_{RUN_ID}@example.com"
    post("/auth/register", {
        "email": enroll_email,
        "password": "password123",
        "first_name": "Enroll",
        "last_name": "Target",
    }, expected_status=201)
    enroll_token = login(enroll_email, "password123")

    code, body = post(f"/courses/{course_id}/enrollments", {
        "user_email": enroll_email,
        "role": "student",
    }, token=teacher_token)
    check(code == 201, "Teacher enrolls user → 201")
    check(body is not None and body.get("role") == "student", "Enrollment has correct role")
    enrolled_user_id = body["user_id"] if body else None

    code, _ = post(f"/courses/{course_id}/enrollments", {
        "user_email": STUDENT_EMAIL,
        "role": "student",
    }, token=enroll_token)
    check(code == 403, "Non-teacher enrolls user → 403")

    code, _ = post(f"/courses/{course_id}/enrollments", {
        "user_email": enroll_email,
        "role": "student",
    }, token=teacher_token)
    check(code == 409, "Duplicate enrollment → 409")

    code, _ = post(f"/courses/{course_id}/enrollments", {
        "user_email": f"nonexistent_{RUN_ID}@example.com",
        "role": "student",
    }, token=teacher_token)
    check(code == 404, "Enroll unknown email → 404")

    fake_course_id = str(uuid.uuid4())
    code, _ = post(f"/courses/{fake_course_id}/enrollments", {
        "user_email": enroll_email,
        "role": "student",
    }, token=teacher_token)
    check(code == 404, "Enroll into nonexistent course → 404")

    # ------------------------------------------------------------------
    section("GET /courses/{course_id}/students")
    # ------------------------------------------------------------------

    code, body = get(f"/courses/{course_id}/students", token=teacher_token)
    check(code == 200, "Teacher lists students → 200")
    check(
        isinstance(body, dict)
        and isinstance(body.get("items"), list)
        and any(item.get("email") == enroll_email for item in body["items"]),
        "Teacher sees newly enrolled user in student list",
    )

    code, body = get(f"/courses/{course_id}/students", token=admin_token)
    check(code == 200, "Admin lists students → 200")
    check(isinstance(body, dict) and isinstance(body.get("items"), list), "Admin receives student page")

    code, _ = get(f"/courses/{course_id}/students", token=student_token)
    check(code == 403, "Non-teacher lists students → 403")

    code, _ = get(f"/courses/{str(uuid.uuid4())}/students", token=teacher_token)
    check(code == 404, "List students for nonexistent course → 404")

    code, _ = get(f"/courses/{course_id}/students")
    check(code == 401, "Unauthenticated list students → 401")

    # ------------------------------------------------------------------
    section("DELETE /courses/{course_id}/enrollments/{user_id}")
    # ------------------------------------------------------------------

    code, _ = delete(f"/courses/{course_id}/enrollments/{enrolled_user_id}", token=enroll_token)
    check(code == 403, "Non-teacher removes student → 403")

    code, _ = delete(f"/courses/{course_id}/enrollments/{enrolled_user_id}", token=teacher_token)
    check(code == 204, "Teacher removes student → 204")

    code, _ = delete(f"/courses/{course_id}/enrollments/{enrolled_user_id}", token=teacher_token)
    check(code == 404, "Remove already-removed enrollment → 404")

    # ------------------------------------------------------------------
    section("DELETE /courses/{course_id}")
    # ------------------------------------------------------------------

    fake_id = str(uuid.uuid4())
    code, _ = delete(f"/courses/{fake_id}", token=teacher_token)
    check(code == 404, "Delete nonexistent course → 404")

    code, _ = delete(f"/courses/{course_id}", token=student_token)
    check(code == 403, "Non-owner deletes course → 403")

    code, _ = delete(f"/courses/{course_id}", token=teacher_token)
    check(code == 204, "Owner deletes course → 204")

    code, _ = delete(f"/courses/{course_id}", token=teacher_token)
    check(code == 404, "Delete already-deleted course → 404")

    code, _ = delete(f"/courses/{second_course_id}", token=teacher_token)
    check(code == 204, "Owner deletes second course → 204")

    summarise()


if __name__ == "__main__":
    main()
