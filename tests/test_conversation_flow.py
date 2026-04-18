"""End-to-end test: login → create conversation → two message turns → print history.

Run from the project root with the server already running:
    python tests/test_conversation_flow.py

Requires SEED_TEST_DATA=true to have been set so the test student and course exist.
"""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8000"

STUDENT_EMAIL = "os_g1_student01@test.com"
STUDENT_PASSWORD = "password123"

FIRST_MESSAGE = "What is a process in operating systems?"
FOLLOW_UP = "Can you explain it in more detail?"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"\nHTTP {exc.code} on {method} {path}")
        print(exc.read().decode())
        sys.exit(1)


def get(path: str, token: str | None = None) -> dict:
    return _request("GET", path, token=token)


def post(path: str, body: dict, token: str | None = None) -> dict:
    return _request("POST", path, body=body, token=token)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def step(label: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")


def main() -> None:
    # 1. Login
    step("1 / 5  Logging in as test student")
    login_resp = post("/auth/login", {"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD})
    token = login_resp["access_token"]
    print(f"  ✓ Token received")

    # 2. Fetch enrolled courses and pick the first one
    step("2 / 5  Fetching enrolled courses")
    enrolled = get("/courses", token=token)
    if not enrolled:
        print("  ✗ No enrolled courses found. Is SEED_TEST_DATA=true and the server restarted?")
        sys.exit(1)
    course = enrolled[0]
    print(f"  ✓ Course: {course['name']} ({course['code']})  id={course['id']}")

    # 3. Create a new conversation
    step("3 / 5  Creating new conversation")
    conv = post("/conversations", {"course_id": course["id"]}, token=token)
    conv_id = conv["id"]
    print(f"  ✓ Conversation id={conv_id}")

    # 4. First message — waits for full RAG response before continuing
    step(f"4 / 5  Sending first message: \"{FIRST_MESSAGE}\"")
    print("  (waiting for RAG response...)")
    ai_msg_1 = post(f"/conversations/{conv_id}/messages", {"content": FIRST_MESSAGE}, token=token)
    print(f"  ✓ AI responded ({len(ai_msg_1['content'])} chars)")

    # 5. Follow-up message
    step(f"5 / 5  Sending follow-up: \"{FOLLOW_UP}\"")
    print("  (waiting for RAG response...)")
    ai_msg_2 = post(f"/conversations/{conv_id}/messages", {"content": FOLLOW_UP}, token=token)
    print(f"  ✓ AI responded ({len(ai_msg_2['content'])} chars)")

    # Print full conversation (messages come back newest-first, reverse for display)
    step("Full conversation")
    history = get(f"/conversations/{conv_id}/messages", token=token)
    for msg in reversed(history["items"]):
        role = "Student" if msg["role"] == "human" else "Tutor"
        print(f"\n  [{role}]\n  {msg['content']}")

    print(f"\n{'─' * 60}")
    print("  Test complete.")
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    main()
