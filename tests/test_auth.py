"""Tests for /auth endpoints (register, login).

Run from the project root with the server already running:
    python tests/test_auth.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.http_client import RUN_ID, check, post, section, summarise


def main() -> None:
    print(f"\nRun ID: {RUN_ID}")

    section("POST /auth/register")

    new_email = f"new_{RUN_ID}@example.com"

    code, body = post("/auth/register", {
        "email": new_email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    })
    check(code == 201, "New user → 201")
    check(body is not None and body.get("email") == new_email, "Response contains correct email")
    check(body is not None and "id" in body, "Response contains id")
    check(body is not None and "hashed_password" not in body, "Response does not leak hashed password")

    code, _ = post("/auth/register", {
        "email": new_email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    })
    check(code == 409, "Duplicate email → 409")

    code, _ = post("/auth/register", {
        "email": f"bad_{RUN_ID}@example.com",
        "password": "short",
        "first_name": "X",
        "last_name": "Y",
    })
    check(code == 422, "Password under 8 characters → 422")

    code, _ = post("/auth/register", {
        "email": "not-an-email",
        "password": "password123",
        "first_name": "X",
        "last_name": "Y",
    })
    check(code == 422, "Invalid email format → 422")

    section("POST /auth/login")

    code, body = post("/auth/login", {"email": new_email, "password": "password123"})
    check(code == 200, "Correct credentials → 200")
    check(body is not None and bool(body.get("access_token")), "Response contains access_token")
    check(body is not None and body.get("token_type") == "bearer", "token_type is 'bearer'")

    code, _ = post("/auth/login", {"email": new_email, "password": "wrongpassword"})
    check(code == 401, "Wrong password → 401")

    code, _ = post("/auth/login", {"email": f"nonexistent_{RUN_ID}@example.com", "password": "password123"})
    check(code == 401, "Unknown email → 401")

    summarise()


if __name__ == "__main__":
    main()
