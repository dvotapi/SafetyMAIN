from __future__ import annotations

from backend.core.domain.entities.organization import Organization
from backend.core.domain.exceptions import OrganizationNotFound
from backend.core.domain.repositories import OrganizationRepositoryContract
from backend.core.domain.value_objects import OrganizationId


class InMemoryOrganizationRepository(OrganizationRepositoryContract):
    def __init__(self) -> None:
        self._organizations_by_id: dict[OrganizationId, Organization] = {}

    def add(self, organization: Organization) -> None:
        self._organizations_by_id[organization.id] = organization

    def get(self, organization_id: OrganizationId) -> Organization:
        organization = self._organizations_by_id.get(organization_id)
        if organization is None:
            raise OrganizationNotFound(organization_id)
        return organization

    def save(self, organization: Organization) -> None:
        if organization.id not in self._organizations_by_id:
            raise OrganizationNotFound(organization.id)
        self._organizations_by_id[organization.id] = organization
