"""User domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    username: str
    firstname: str
    surname: str
    salt_hex: str
    password_hash_hex: str
    role: str = "student"

    @property
    def name(self) -> str:
        parts = [self.firstname.strip(), self.surname.strip()]
        return " ".join(part for part in parts if part)
