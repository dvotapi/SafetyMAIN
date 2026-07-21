from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.organization import Organization


@dataclass(frozen=True, slots=True)
class OrganizationListCriteria:
    offset: int
    limit: int
    is_active: bool | None = None
    name: str | None = None
    sort_ascending: bool = False


@dataclass(frozen=True, slots=True)
class OrganizationListResult:
    items: tuple[Organization, ...]
    total: int
    offset: int
    limit: int
