from __future__ import annotations

from backend.core.application.queries.get_organization import GetOrganizationQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.organization import Organization


class GetOrganizationHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetOrganizationQuery) -> Organization:
        return self._unit_of_work.organizations.get(query.organization_id)
