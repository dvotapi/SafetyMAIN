from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import UserId


class UserError(SafetyMainDomainError):
    """Base class for User domain errors."""


class UserNotFound(UserError):
    def __init__(self, user_id: UserId) -> None:
        self.user_id = user_id
        super().__init__(f"User was not found: {user_id.value}")
