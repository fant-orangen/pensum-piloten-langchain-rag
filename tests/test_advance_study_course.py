"""Tests for POST /courses/advance (study-course rotation).

Runs against a live server seeded with the operating-systems experiment
cohort (SEED_TEST_DATA=true). Advancing a study student is idempotent as a
3-cycle (os_g1 -> os_g2 -> os_g3 -> os_g1), so this test restores the
seeded state by always cycling a multiple of three times.

Usage:
    python tests/test_advance_study_course.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.http_client import RUN_ID, check, get, login, post, section, summarise

STUDY_STUDENT_EMAIL = "g1u12@test.com"
STUDY_STUDENT_PASSWORD = "password123"
TEACHER_EMAIL = "teacher@test.com"
TEACHER_PASSWORD = "password123"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "password123"

EXPECTED_CYCLE = ["os_g1", "os_g2", "os_g3", "os_g1"]


def _current_course_code(token: str) -> str | None:
    """Return the code of the single study course the caller is enrolled in, if any."""
    code_status, body = get("/courses", token=token)
    if code_status != 200 or not isinstance(body, list) or len(body) != 1:
        return None
    first = body[0]
    return first.get("code") if isinstance(first, dict) else None


def main() -> None:
    print(f"\nRun ID: {RUN_ID}")

    student_token = login(STUDY_STUDENT_EMAIL, STUDY_STUDENT_PASSWORD)
    teacher_token = login(TEACHER_EMAIL, TEACHER_PASSWORD)
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)

    section("POST /courses/advance — auth")

    code, _ = post("/courses/advance")
    check(code == 401, "Unauthenticated → 401")

    section("POST /courses/advance — study student full cycle (g1 -> g2 -> g3 -> g1)")

    starting_code = _current_course_code(student_token)
    check(
        starting_code == EXPECTED_CYCLE[0],
        f"Student starts in {EXPECTED_CYCLE[0]}",
        detail=f"got {starting_code!r}",
    )

    for step_index, expected_next in enumerate(EXPECTED_CYCLE[1:], start=1):
        code, body = post("/courses/advance", token=student_token)
        check(code == 200, f"Advance step {step_index} → 200")
        check(
            isinstance(body, dict) and body.get("code") == expected_next,
            f"Advance step {step_index} returns {expected_next}",
            detail=f"got {body!r}",
        )

        current_code = _current_course_code(student_token)
        check(
            current_code == expected_next,
            f"GET /courses reflects enrollment in {expected_next} after step {step_index}",
            detail=f"got {current_code!r}",
        )

    check(
        _current_course_code(student_token) == EXPECTED_CYCLE[0],
        "Cycle completed — student is back in the starting course",
    )

    section("POST /courses/advance — non-study callers rejected")

    code, _ = post("/courses/advance", token=teacher_token)
    check(code == 409, "Teacher (no student enrollments) → 409")

    code, _ = post("/courses/advance", token=admin_token)
    check(code == 409, "Admin (no student enrollments) → 409")

    summarise()


if __name__ == "__main__":
    main()
