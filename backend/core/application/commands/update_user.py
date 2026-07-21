from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    user_id: UserId
    display_name: str | None = None
    email: str | None = None
    is_active: bool | None = None
