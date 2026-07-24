from __future__ import annotations

from backend.core.application.queries.risk_controls import (
    GetRiskControlQuery,
    ListRiskControlsQuery,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_control import RiskControlNotFound
from backend.core.domain.value_objects.risk_control_query import (
    RiskControlPage,
    RiskControlQuery,
)


class GetRiskControlHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetRiskControlQuery) -> RiskControl:
        control = self._unit_of_work.risk_controls.get(
            query.organization_id,
            query.control_id,
        )
        if control is None:
            raise RiskControlNotFound(query.control_id)
        return control


class ListRiskControlsHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, query: ListRiskControlsQuery) -> RiskControlPage:
        as_of = self._clock.now() if self._clock is not None else None
        return self._unit_of_work.risk_controls.list(
            RiskControlQuery(
                organization_id=query.organization_id,
                hazard_id=query.hazard_id,
                risk_assessment_id=query.risk_assessment_id,
                status=query.status,
                hierarchy_level=query.hierarchy_level,
                control_nature=query.control_nature,
                owner_reference=query.owner_reference,
                latest_effectiveness_result=query.latest_effectiveness_result,
                review_due_before=query.review_due_before,
                review_due_after=query.review_due_after,
                overdue_only=query.overdue_only,
                awaiting_verification=query.awaiting_verification,
                include_terminal=query.include_terminal,
                search=query.search,
                as_of=as_of,
                offset=query.offset,
                limit=query.limit,
            )
        )
