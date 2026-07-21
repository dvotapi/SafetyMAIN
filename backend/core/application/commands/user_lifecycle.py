from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class ActivateUserCommand:
    user_id: UserId


@dataclass(frozen=True, slots=True)
class DeactivateUserCommand:
    user_id: UserId
