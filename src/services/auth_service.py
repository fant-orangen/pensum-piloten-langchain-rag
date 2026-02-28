"""Authentication services."""

from __future__ import annotations

import hashlib
import hmac
import os

from src.domain import User
from src.storage import load_users, save_users

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    ).hex()


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False

    actual_hash_hex = hash_password(password, salt)
    return hmac.compare_digest(actual_hash_hex, expected_hash_hex)


def login_user(username: str, password: str) -> tuple[bool, str, User | None]:
    cleaned_username = username.strip()
    if not cleaned_username or not password:
        return False, "Fyll ut alle feltene.", None

    users = load_users()
    user = users.get(cleaned_username)
    if user is None or not verify_password(password, user.salt_hex, user.password_hash_hex):
        return False, "Feil brukernavn eller passord.", None

    return True, "Du er nå logget inn.", user


def register_user(
    username: str,
    password: str,
    password_confirm: str,
    fornavn: str,
    etternavn: str,
) -> tuple[bool, str, User | None]:
    cleaned_username = username.strip()
    cleaned_fornavn = fornavn.strip()
    cleaned_etternavn = etternavn.strip()
    if not cleaned_username or not password or not password_confirm or not cleaned_fornavn or not cleaned_etternavn:
        return False, "Fyll ut alle feltene.", None
    if password != password_confirm:
        return False, "Passordene er ikke like.", None

    users = load_users()
    if cleaned_username in users:
        return False, "Brukernavn finnes allerede.", None

    salt = os.urandom(16)
    user = User(
        username=cleaned_username,
        fornavn=cleaned_fornavn,
        etternavn=cleaned_etternavn,
        salt_hex=salt.hex(),
        password_hash_hex=hash_password(password, salt),
    )
    users[cleaned_username] = user
    save_users(users)

    return True, "Registrering fullført. Du er nå logget inn.", user


def logout_user() -> str:
    return "Du er logget ut."
