from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class GetUserQuery:
    user_id: UserId
