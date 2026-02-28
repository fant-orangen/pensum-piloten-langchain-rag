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
        firstname = user_data.get("firstname")
        surname = user_data.get("surname")
        legacy_firstname = user_data.get("fornavn")
        legacy_surname = user_data.get("etternavn")
        name = user_data.get("name")
        password_hash = user_data.get("password_hash")
        salt = user_data.get("salt")
        if (
            isinstance(stored_username, str)
            and stored_username
            and isinstance(password_hash, str)
            and password_hash
            and isinstance(salt, str)
            and salt
        ):
            resolved_firstname = ""
            resolved_surname = ""
            if isinstance(firstname, str) and firstname:
                resolved_firstname = firstname
                if isinstance(surname, str):
                    resolved_surname = surname
            elif isinstance(legacy_firstname, str) and legacy_firstname:
                resolved_firstname = legacy_firstname
                if isinstance(legacy_surname, str):
                    resolved_surname = legacy_surname
            elif isinstance(name, str) and name:
                resolved_firstname = name

            users[username] = User(
                username=stored_username,
                firstname=resolved_firstname,
                surname=resolved_surname,
                salt_hex=salt,
                password_hash_hex=password_hash,
            )
    return users


def save_users(users: dict[str, User]) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        username: {
            "username": user.username,
            "firstname": user.firstname,
            "surname": user.surname,
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
