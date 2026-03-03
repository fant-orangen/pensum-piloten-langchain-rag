"""Authentication services."""

from __future__ import annotations

import hashlib
import hmac
import os

from src.domain import User
from src.storage import load_users, save_users

PBKDF2_ITERATIONS = 200_000
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_ENV = "ADMIN_PASSWORD"


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


def ensure_admin_user() -> bool:
    users = load_users()
    existing_admin = users.get(ADMIN_USERNAME)
    if existing_admin is not None:
        if existing_admin.role != "admin":
            users[ADMIN_USERNAME] = User(
                username=existing_admin.username,
                firstname=existing_admin.firstname,
                surname=existing_admin.surname,
                salt_hex=existing_admin.salt_hex,
                password_hash_hex=existing_admin.password_hash_hex,
                role="admin",
            )
            save_users(users)
        return True

    admin_password = os.getenv(ADMIN_PASSWORD_ENV, "")
    if not admin_password:
        return False

    salt = os.urandom(16)
    users[ADMIN_USERNAME] = User(
        username=ADMIN_USERNAME,
        firstname="Admin",
        surname="",
        salt_hex=salt.hex(),
        password_hash_hex=hash_password(admin_password, salt),
        role="admin",
    )
    save_users(users)
    return True


def login_user(username: str, password: str) -> tuple[bool, str, User | None]:
    cleaned_username = username.strip()
    if not cleaned_username or not password:
        return False, "Fyll ut alle feltene.", None

    admin_ready = ensure_admin_user()

    users = load_users()
    user = users.get(cleaned_username)
    if cleaned_username == ADMIN_USERNAME and user is None and not admin_ready:
        return False, "Admin-bruker er ikke satt opp. Sett ADMIN_PASSWORD og start på nytt.", None
    if user is None or not verify_password(password, user.salt_hex, user.password_hash_hex):
        return False, "Feil brukernavn eller passord.", None

    return True, "Du er nå logget inn.", user


def register_user(
    username: str,
    password: str,
    password_confirm: str,
    firstname: str,
    surname: str,
) -> tuple[bool, str, User | None]:
    cleaned_username = username.strip()
    cleaned_firstname = firstname.strip()
    cleaned_surname = surname.strip()
    if not cleaned_username or not password or not password_confirm or not cleaned_firstname or not cleaned_surname:
        return False, "Fyll ut alle feltene.", None
    if password != password_confirm:
        return False, "Passordene er ikke like.", None
    if cleaned_username == ADMIN_USERNAME:
        return False, "Ikke tillatt.", None

    users = load_users()
    if cleaned_username in users:
        return False, "Brukernavn finnes allerede.", None

    salt = os.urandom(16)
    user = User(
        username=cleaned_username,
        firstname=cleaned_firstname,
        surname=cleaned_surname,
        salt_hex=salt.hex(),
        password_hash_hex=hash_password(password, salt),
        role="student",
    )
    users[cleaned_username] = user
    save_users(users)

    return True, "Registrering fullført. Du er nå logget inn.", user


def upgrade_user_to_teacher(username: str) -> tuple[bool, str]:
    cleaned_username = username.strip()
    users = load_users()
    user = users.get(cleaned_username)
    if user is None:
        return False, "Fant ikke brukeren."
    if user.role == "admin" or cleaned_username == ADMIN_USERNAME:
        return False, "Ikke tillatt."
    if user.role == "teacher":
        return False, "Brukeren er allerede lærer."

    users[cleaned_username] = User(
        username=user.username,
        firstname=user.firstname,
        surname=user.surname,
        salt_hex=user.salt_hex,
        password_hash_hex=user.password_hash_hex,
        role="teacher",
    )
    save_users(users)
    return True, "Brukeren er oppgradert til lærer."


def logout_user() -> str:
    return "Du er logget ut."
