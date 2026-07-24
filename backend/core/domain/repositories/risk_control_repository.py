from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_control_code import RiskControlCode
from backend.core.domain.value_objects.risk_control_query import (
    RiskControlPage,
    RiskControlQuery,
)
from backend.core.domain.value_objects.safety_ids import (
    RiskAssessmentId,
    RiskControlId,
)


class RiskControlRepositoryContract(Protocol):
    """Organization-scoped risk control persistence contract."""

    def add(self, control: RiskControl) -> None:
        ...

    def get(
        self,
        organization_id: OrganizationId,
        control_id: RiskControlId,
    ) -> RiskControl | None:
        ...

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: RiskControlCode,
    ) -> RiskControl | None:
        ...

    def list(self, query: RiskControlQuery) -> RiskControlPage:
        ...

    def exists_for_source(
        self,
        organization_id: OrganizationId,
        risk_assessment_id: RiskAssessmentId,
        source_control_reference: str,
    ) -> bool:
        ...

    def save(self, control: RiskControl, *, expected_version: int) -> None:
        ...
