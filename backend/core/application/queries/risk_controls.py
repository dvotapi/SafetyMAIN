from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlType,
    EffectivenessResult,
    RiskControlStatus,
)
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)


@dataclass(frozen=True, slots=True)
class GetRiskControlQuery:
    organization_id: OrganizationId
    control_id: RiskControlId


@dataclass(frozen=True, slots=True)
class ListRiskControlsQuery:
    organization_id: OrganizationId
    hazard_id: HazardId | None = None
    risk_assessment_id: RiskAssessmentId | None = None
    status: RiskControlStatus | None = None
    hierarchy_level: ControlType | None = None
    control_nature: ControlNature | None = None
    owner_reference: str | None = None
    latest_effectiveness_result: EffectivenessResult | None = None
    review_due_before: datetime | None = None
    review_due_after: datetime | None = None
    overdue_only: bool = False
    awaiting_verification: bool = False
    include_terminal: bool = False
    search: str | None = None
    offset: int = 0
    limit: int = 50
