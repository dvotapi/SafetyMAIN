from __future__ import annotations

from backend.core.domain.entities.organization import Organization, normalized_organization_name_key
from backend.core.domain.exceptions import OrganizationNotFound
from backend.core.domain.repositories import OrganizationRepositoryContract
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.organization_list_criteria import (
    OrganizationListCriteria,
    OrganizationListResult,
)


class InMemoryOrganizationRepository(OrganizationRepositoryContract):
    def __init__(self) -> None:
        self._organizations_by_id: dict[OrganizationId, Organization] = {}
        self._organizations_by_normalized_name: dict[str, OrganizationId] = {}

    def add(self, organization: Organization) -> None:
        self._organizations_by_id[organization.id] = organization
        self._organizations_by_normalized_name[
            normalized_organization_name_key(organization.name)
        ] = organization.id

    def get(self, organization_id: OrganizationId) -> Organization:
        organization = self._organizations_by_id.get(organization_id)
        if organization is None:
            raise OrganizationNotFound(organization_id)
        return organization

    def get_by_normalized_name(self, normalized_name: str) -> Organization | None:
        organization_id = self._organizations_by_normalized_name.get(
            normalized_name.strip().casefold()
        )
        if organization_id is None:
            return None
        return self._organizations_by_id.get(organization_id)

    def save(self, organization: Organization) -> None:
        if organization.id not in self._organizations_by_id:
            raise OrganizationNotFound(organization.id)
        previous = self._organizations_by_id[organization.id]
        previous_key = normalized_organization_name_key(previous.name)
        next_key = normalized_organization_name_key(organization.name)
        if previous_key != next_key:
            del self._organizations_by_normalized_name[previous_key]
            self._organizations_by_normalized_name[next_key] = organization.id
        self._organizations_by_id[organization.id] = organization

    def list_organizations(self, criteria: OrganizationListCriteria) -> OrganizationListResult:
        organizations = list(self._organizations_by_id.values())

        if criteria.is_active is not None:
            organizations = [
                organization
                for organization in organizations
                if organization.is_active() == criteria.is_active
            ]
        if criteria.name is not None:
            needle = criteria.name.strip().casefold()
            organizations = [
                organization
                for organization in organizations
                if needle in organization.name.casefold()
            ]

        organizations.sort(key=lambda organization: organization.id.value)
        organizations.sort(
            key=lambda organization: organization.created_at,
            reverse=not criteria.sort_ascending,
        )
        total = len(organizations)
        page = organizations[criteria.offset : criteria.offset + criteria.limit]

        return OrganizationListResult(
            items=tuple(page),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )
