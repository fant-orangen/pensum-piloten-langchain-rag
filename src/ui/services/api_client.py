"""Shared HTTP client for the Gradio UI → FastAPI backend.

All requests go through _request().  Authenticated callers pass the JWT
token and it is forwarded as ``Authorization: Bearer <token>``.

On a 401 response an ApiUnauthorizedError is raised so call sites can
redirect the user to the login page.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class ApiError(Exception):
    """Raised when the backend returns an unexpected HTTP error."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class ApiUnauthorizedError(ApiError):
    """Raised specifically on HTTP 401 so callers can redirect to login."""

    def __init__(self) -> None:
        super().__init__(401, "Session expired — please log in again.")


def _base_url() -> str:
    url = os.getenv("API_BASE_URL", "http://localhost:8000")
    return url.rstrip("/")


def _parse_body(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode(errors="replace")


def _detail_from_body(body: Any) -> str:
    if isinstance(body, dict):
        return str(body.get("detail", body))
    if isinstance(body, str):
        return body
    return "An unexpected error occurred."


def request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> Any:
    """Send an HTTP request and return the parsed response body.

    Raises:
        ApiUnauthorizedError: on HTTP 401.
        ApiError: on any other non-2xx response.
    """
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers: dict[str, str] = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{_base_url()}{path}"
    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return _parse_body(resp.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        parsed = _parse_body(raw)
        if exc.code == 401:
            raise ApiUnauthorizedError() from exc
        raise ApiError(exc.code, _detail_from_body(parsed)) from exc
    except urllib.error.URLError as exc:
        raise ApiError(0, f"Could not connect to API server: {exc.reason}") from exc


def get(path: str, *, token: str | None = None) -> Any:
    return request("GET", path, token=token)


def post(path: str, body: dict[str, Any] | None = None, *, token: str | None = None) -> Any:
    return request("POST", path, body=body, token=token)


def delete(path: str, *, token: str | None = None) -> Any:
    return request("DELETE", path, token=token)
