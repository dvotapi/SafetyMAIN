from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.organization import Organization
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.organization_list_criteria import (
    OrganizationListCriteria,
    OrganizationListResult,
)


class OrganizationRepositoryContract(Protocol):
    """Repository contract for tenant organizations."""

    def add(self, organization: Organization) -> None:
        ...

    def get(self, organization_id: OrganizationId) -> Organization:
        ...

    def get_by_normalized_name(self, normalized_name: str) -> Organization | None:
        ...

    def save(self, organization: Organization) -> None:
        ...

    def list_organizations(
        self,
        criteria: OrganizationListCriteria,
    ) -> OrganizationListResult:
        ...
