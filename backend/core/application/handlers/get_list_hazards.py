from __future__ import annotations

from backend.core.application.queries.hazards import GetHazardQuery, ListHazardsQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.exceptions.hazard import HazardNotFound
from backend.core.domain.value_objects.hazard_query import HazardPage, HazardQuery


class GetHazardHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetHazardQuery) -> Hazard:
        hazard = self._unit_of_work.hazards.get(
            query.organization_id,
            query.hazard_id,
        )
        if hazard is None:
            raise HazardNotFound(query.hazard_id)
        return hazard


class ListHazardsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListHazardsQuery) -> HazardPage:
        return self._unit_of_work.hazards.list(
            HazardQuery(
                organization_id=query.organization_id,
                status=query.status,
                category=query.category,
                safety_direction=query.safety_direction,
                source=query.source,
                affected_subject=query.affected_subject,
                identified_from=query.identified_from,
                identified_to=query.identified_to,
                created_from=query.created_from,
                created_to=query.created_to,
                search=query.search,
                include_archived=query.include_archived,
                offset=query.offset,
                limit=query.limit,
            )
        )
