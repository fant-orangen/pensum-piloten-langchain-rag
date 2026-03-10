"""Shared HTTP helpers and test reporting for endpoint tests.

Each test module imports from here. Run individual test files directly:
    python tests/test_auth.py
    python tests/test_courses.py
    python tests/test_conversations.py
"""

import json
import sys
import time
import uuid
import urllib.error
import urllib.request
from typing import Any


def _parse(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode(errors="replace")

BASE = "http://localhost:8000"

# Unique suffix so each test run creates non-conflicting resources.
RUN_ID = str(int(time.time()))[-6:]

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _request(
    method: str,
    path: str,
    body: dict | None = None,
    token: str | None = None,
    expected_status: int | None = None,
) -> tuple[int, Any]:
    """Send a request; return (status_code, parsed_body).

    If expected_status is set and the actual code differs, the process exits —
    use this for setup calls that must succeed before tests can run.
    """
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            code = resp.status
            parsed = _parse(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        code = exc.code
        parsed = _parse(raw)

    if expected_status is not None and code != expected_status:
        print(f"\n  SETUP FAILED  {method} {path}")
        print(f"  Expected {expected_status}, got {code}: {parsed}")
        sys.exit(1)

    return code, parsed


def get(path, token=None, expected_status=None):
    return _request("GET", path, token=token, expected_status=expected_status)

def post(path, body=None, token=None, expected_status=None):
    return _request("POST", path, body=body, token=token, expected_status=expected_status)


def post_multipart(path, files, fields=None, token=None, expected_status=None):
    """Send multipart/form-data with one or more files.

    files: iterable of tuples (field_name, filename, bytes_content, content_type)
    """
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    parts: list[bytes] = []

    for name, value in (fields or {}).items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(str(value).encode())
        parts.append(b"\r\n")

    for field_name, filename, content, content_type in files:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode()
        )
        parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        parts.append(content)
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    data = b"".join(parts)

    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            code = resp.status
            parsed = _parse(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        code = exc.code
        parsed = _parse(raw)

    if expected_status is not None and code != expected_status:
        print(f"\n  SETUP FAILED  POST {path} (multipart)")
        print(f"  Expected {expected_status}, got {code}: {parsed}")
        sys.exit(1)

    return code, parsed

def delete(path, token=None, expected_status=None):
    return _request("DELETE", path, token=token, expected_status=expected_status)


def login(email: str, password: str) -> str:
    """Log in and return the access token. Exits on failure."""
    _, body = post("/auth/login", {"email": email, "password": password}, expected_status=200)
    return body["access_token"]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_passed = 0
_failed = 0


def check(condition: bool, label: str, detail: str = "") -> bool:
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS  {label}")
    else:
        _failed += 1
        print(f"  FAIL  {label}" + (f"\n        {detail}" if detail else ""))
    return condition


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def summarise() -> None:
    total = _passed + _failed
    print(f"\n{'─' * 60}")
    suffix = f"  ({_failed} failed)" if _failed else "  — all passed"
    print(f"  {_passed}/{total} passed{suffix}")
    print(f"{'─' * 60}\n")
    if _failed:
        sys.exit(1)
