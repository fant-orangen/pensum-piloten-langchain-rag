"""JSON-backed user persistence."""

from __future__ import annotations

import json
from pathlib import Path

from src.domain import User

USERS_PATH = Path("data/users.json")


def load_users() -> dict[str, User]:
    if not USERS_PATH.exists():
        return {}

    try:
        payload = json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(payload, dict):
        return {}

    users: dict[str, User] = {}
    for username, user_data in payload.items():
        if not isinstance(username, str) or not isinstance(user_data, dict):
            continue

        stored_username = user_data.get("username")
        name = user_data.get("name")
        password_hash = user_data.get("password_hash")
        salt = user_data.get("salt")
        if all(
            isinstance(value, str) and value
            for value in (stored_username, name, password_hash, salt)
        ):
            users[username] = User(
                username=stored_username,
                name=name,
                salt_hex=salt,
                password_hash_hex=password_hash,
            )
    return users


def save_users(users: dict[str, User]) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        username: {
            "username": user.username,
            "name": user.name,
            "password_hash": user.password_hash_hex,
            "salt": user.salt_hex,
        }
        for username, user in users.items()
    }
    USERS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
