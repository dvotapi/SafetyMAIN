from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.user import User
from backend.core.domain.value_objects import UserId


class UserLookupPort(Protocol):
    """Application port for resolving platform users."""

    def get_user(self, user_id: UserId) -> User:
        ...

    def get_user_by_external_subject(self, external_subject: str) -> User | None:
        ...
