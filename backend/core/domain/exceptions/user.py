from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import UserId


class UserError(SafetyMainDomainError):
    """Base class for User domain errors."""


class UserNotFound(UserError):
    def __init__(self, user_id: UserId) -> None:
        self.user_id = user_id
        super().__init__(f"User was not found: {user_id.value}")


class DuplicateUserEmail(UserError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__("User email already exists.")


class UserAlreadyActive(UserError):
    def __init__(self, user_id: UserId) -> None:
        self.user_id = user_id
        super().__init__("User is already active.")


class UserAlreadyDeactivated(UserError):
    def __init__(self, user_id: UserId) -> None:
        self.user_id = user_id
        super().__init__("User is already deactivated.")
