from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListOrganizationsQuery:
    offset: int
    limit: int
    is_active: bool | None = None
    name: str | None = None
    sort_ascending: bool = False
