from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListUsersQuery:
    offset: int = 0
    limit: int = 50
    is_active: bool | None = None
    email: str | None = None
    display_name: str | None = None
    sort_ascending: bool = False
