from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import (
    AssessmentProfileCode,
    RiskAssessmentStatus,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId


@dataclass(frozen=True, slots=True)
class GetRiskAssessmentQuery:
    organization_id: OrganizationId
    risk_assessment_id: RiskAssessmentId


@dataclass(frozen=True, slots=True)
class ListRiskAssessmentsQuery:
    organization_id: OrganizationId
    hazard_id: HazardId | None = None
    status: RiskAssessmentStatus | None = None
    assessment_profile: AssessmentProfileCode | None = None
    assessed_object_type: str | None = None
    include_archived: bool = False
    include_superseded: bool = True
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    offset: int = 0
    limit: int = 50
