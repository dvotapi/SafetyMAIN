from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class UserListCriteria:
    offset: int
    limit: int
    is_active: bool | None = None
    email: str | None = None
    display_name: str | None = None
    sort_ascending: bool = False


@dataclass(frozen=True, slots=True)
class UserListResult:
    items: tuple[User, ...]
    total: int
    offset: int
    limit: int
