from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.user import User
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.user_list_criteria import (
    UserListCriteria,
    UserListResult,
)


class UserRepositoryContract(Protocol):
    """Repository contract for platform users."""

    def add(self, user: User) -> None:
        ...

    def get(self, user_id: UserId) -> User:
        ...

    def get_by_email(self, email: str) -> User | None:
        ...

    def save(self, user: User) -> None:
        ...

    def list_users(self, criteria: UserListCriteria) -> UserListResult:
        ...
