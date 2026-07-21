from __future__ import annotations

from backend.core.domain.entities.user import User
from backend.core.domain.exceptions import UserNotFound
from backend.core.domain.repositories import UserRepositoryContract
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.user_list_criteria import (
    UserListCriteria,
    UserListResult,
)


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

    def list_users(self, criteria: UserListCriteria) -> UserListResult:
        users = list(self._users_by_id.values())

        if criteria.is_active is not None:
            users = [user for user in users if user.is_active() == criteria.is_active]
        if criteria.email is not None:
            needle = criteria.email.strip().lower()
            users = [user for user in users if needle in user.email]
        if criteria.display_name is not None:
            needle = criteria.display_name.strip().lower()
            users = [user for user in users if needle in user.display_name.lower()]

        users.sort(
            key=lambda user: user.created_at,
            reverse=not criteria.sort_ascending,
        )
        total = len(users)
        page = users[criteria.offset : criteria.offset + criteria.limit]

        return UserListResult(
            items=tuple(page),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

    def snapshot(self) -> tuple[dict[UserId, User], dict[str, UserId]]:
        return (dict(self._users_by_id), dict(self._users_by_email))

    def restore(self, snapshot: tuple[dict[UserId, User], dict[str, UserId]]) -> None:
        users_by_id, users_by_email = snapshot
        self._users_by_id = dict(users_by_id)
        self._users_by_email = dict(users_by_email)
