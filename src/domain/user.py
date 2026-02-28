"""User domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    username: str
    name: str
    salt_hex: str
    password_hash_hex: str
