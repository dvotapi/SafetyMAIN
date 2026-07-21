from __future__ import annotations

from backend.core.domain.entities.user import User
from backend.core.domain.exceptions import UserNotFound
from backend.core.domain.repositories import UserRepositoryContract
from backend.core.domain.value_objects import UserId


class InMemoryUserRepository(UserRepositoryContract):
    def __init__(self) -> None:
        self._users_by_id: dict[UserId, User] = {}
        self._users_by_email: dict[str, UserId] = {}

    def add(self, user: User) -> None:
        self._users_by_id[user.id] = user
        self._users_by_email[user.email] = user.id

    def get(self, user_id: UserId) -> User:
        user = self._users_by_id.get(user_id)
        if user is None:
            raise UserNotFound(user_id)
        return user

    def get_by_email(self, email: str) -> User | None:
        user_id = self._users_by_email.get(email.strip().lower())
        if user_id is None:
            return None
        return self._users_by_id.get(user_id)

    def save(self, user: User) -> None:
        if user.id not in self._users_by_id:
            raise UserNotFound(user.id)
        previous = self._users_by_id[user.id]
        if previous.email != user.email:
            del self._users_by_email[previous.email]
            self._users_by_email[user.email] = user.id
        self._users_by_id[user.id] = user
