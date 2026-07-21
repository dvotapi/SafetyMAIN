from __future__ import annotations

from backend.core.contracts.user_credentials import UserCredentialsPort
from backend.core.contracts.user_lookup import UserLookupPort
from backend.core.domain.entities.user import User
from backend.core.domain.exceptions import UserNotFound
from backend.core.domain.value_objects import UserId


class InMemoryIdentityStore(UserLookupPort, UserCredentialsPort):
    """In-memory identity adapter for development and tests."""

    def __init__(self) -> None:
        self._users_by_id: dict[UserId, User] = {}
        self._users_by_email: dict[str, UserId] = {}
        self._users_by_external_subject: dict[str, UserId] = {}
        self._password_hashes: dict[UserId, str] = {}

    def register_user(self, user: User, password_hash: str) -> None:
        self._users_by_id[user.id] = user
        self._users_by_email[user.email] = user.id
        self._password_hashes[user.id] = password_hash
        if user.external_subject is not None:
            self._users_by_external_subject[user.external_subject] = user.id

    def get_user(self, user_id: UserId) -> User:
        user = self._users_by_id.get(user_id)
        if user is None:
            raise UserNotFound(user_id)
        return user

    def get_user_by_email(self, email: str) -> User | None:
        user_id = self._users_by_email.get(email.strip().lower())
        if user_id is None:
            return None
        return self._users_by_id.get(user_id)

    def get_user_by_external_subject(self, external_subject: str) -> User | None:
        user_id = self._users_by_external_subject.get(external_subject)
        if user_id is None:
            return None
        return self._users_by_id.get(user_id)

    def get_password_hash(self, user_id: UserId) -> str | None:
        return self._password_hashes.get(user_id)
