from __future__ import annotations

from typing import Protocol


class PasswordHasherContract(Protocol):
    """Contract for password hashing and verification."""

    def hash_password(self, password: str) -> str:
        ...

    def verify_password(self, password: str, password_hash: str) -> bool:
        ...
