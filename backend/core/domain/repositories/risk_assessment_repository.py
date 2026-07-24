from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.risk_assessment_components import AssessedObjectRef
from backend.core.domain.value_objects.risk_assessment_query import (
    RiskAssessmentPage,
    RiskAssessmentQuery,
)
from backend.core.domain.value_objects.safety_enums import AssessmentProfileCode
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId


class RiskAssessmentRepositoryContract(Protocol):
    """Organization-scoped risk assessment persistence contract."""

    def add(self, assessment: RiskAssessment) -> None:
        ...

    def get(
        self,
        organization_id: OrganizationId,
        risk_assessment_id: RiskAssessmentId,
    ) -> RiskAssessment | None:
        ...

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: RiskAssessmentCode,
    ) -> RiskAssessment | None:
        ...

    def list(self, query: RiskAssessmentQuery) -> RiskAssessmentPage:
        ...

    def list_approved_for_scope(
        self,
        *,
        organization_id: OrganizationId,
        hazard_id: HazardId,
        assessment_profile: AssessmentProfileCode,
        assessed_object: AssessedObjectRef,
    ) -> tuple[RiskAssessment, ...]:
        ...

    def save(self, assessment: RiskAssessment, *, expected_version: int) -> None:
        ...
