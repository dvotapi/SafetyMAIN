from __future__ import annotations

from backend.core.application.queries.list_organizations import ListOrganizationsQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects.organization_list_criteria import (
    OrganizationListCriteria,
    OrganizationListResult,
)


class ListOrganizationsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListOrganizationsQuery) -> OrganizationListResult:
        criteria = OrganizationListCriteria(
            offset=query.offset,
            limit=query.limit,
            is_active=query.is_active,
            name=query.name,
            sort_ascending=query.sort_ascending,
        )
        return self._unit_of_work.organizations.list_organizations(criteria)
