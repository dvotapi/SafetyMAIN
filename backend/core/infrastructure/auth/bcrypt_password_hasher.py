from __future__ import annotations

import bcrypt

from backend.core.contracts.password_hasher import PasswordHasherContract


class BcryptPasswordHasher:
    """Bcrypt-backed password hasher."""

    def hash_password(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )


def create_password_hasher() -> PasswordHasherContract:
    return BcryptPasswordHasher()
