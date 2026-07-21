from __future__ import annotations

from typing import Protocol

from backend.core.domain.value_objects import UserId


class UserCredentialsPort(Protocol):
    """Application port for resolving stored user credentials."""

    def get_password_hash(self, user_id: UserId) -> str | None:
        ...
