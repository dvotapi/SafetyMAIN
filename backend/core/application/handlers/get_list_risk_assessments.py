from __future__ import annotations

from backend.core.application.queries.risk_assessments import (
    GetRiskAssessmentQuery,
    ListRiskAssessmentsQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import RiskAssessmentNotFound
from backend.core.domain.value_objects.risk_assessment_query import (
    RiskAssessmentPage,
    RiskAssessmentQuery,
)


class GetRiskAssessmentHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetRiskAssessmentQuery) -> RiskAssessment:
        assessment = self._unit_of_work.risk_assessments.get(
            query.organization_id,
            query.risk_assessment_id,
        )
        if assessment is None:
            raise RiskAssessmentNotFound(query.risk_assessment_id)
        return assessment


class ListRiskAssessmentsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListRiskAssessmentsQuery) -> RiskAssessmentPage:
        return self._unit_of_work.risk_assessments.list(
            RiskAssessmentQuery(
                organization_id=query.organization_id,
                hazard_id=query.hazard_id,
                status=query.status,
                assessment_profile=query.assessment_profile,
                assessed_object_type=query.assessed_object_type,
                include_archived=query.include_archived,
                include_superseded=query.include_superseded,
                search=query.search,
                created_from=query.created_from,
                created_to=query.created_to,
                offset=query.offset,
                limit=query.limit,
            )
        )
