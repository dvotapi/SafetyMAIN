from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.organization import Organization
from backend.core.domain.value_objects import OrganizationId


class OrganizationRepositoryContract(Protocol):
    """Repository contract for tenant organizations."""

    def add(self, organization: Organization) -> None:
        ...

    def get(self, organization_id: OrganizationId) -> Organization:
        ...

    def save(self, organization: Organization) -> None:
        ...
