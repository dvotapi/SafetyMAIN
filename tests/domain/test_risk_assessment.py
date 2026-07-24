from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import (
    RiskAssessmentAlreadyApproved,
    RiskAssessmentInherentRiskRequired,
)
from backend.core.domain.services.assessment_profiles import (
    get_assessment_profile,
    resolve_matrix_level,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
    RiskAcceptance,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    RiskAcceptanceDecision,
    RiskAssessmentStatus,
    RiskLevel,
)
from backend.core.domain.value_objects.safety_ids import HazardId


def test_matrix_profiles_resolve_levels() -> None:
    assert resolve_matrix_level(matrix_size=3, probability_score=3, severity_score=3) is RiskLevel.EXTREME
    assert resolve_matrix_level(matrix_size=5, probability_score=2, severity_score=2) is RiskLevel.LOW
    profile = get_assessment_profile(AssessmentProfileCode.RUSSIAN_OCCUPATIONAL_RISK)
    assert profile.matrix_size == 5
    assert profile.default_review_frequency_days == 365


def test_risk_assessment_approve_requires_inherent_and_acceptance() -> None:
    now = datetime.now(UTC)
    assessment = RiskAssessment.create(
        organization_id=OrganizationId(value=uuid4()),
        hazard_id=HazardId(value=uuid4()),
        code="RA-UT-1",
        title="Unit test assessment",
        assessment_profile=AssessmentProfileCode.SIMPLE_5X5,
        assessed_object=AssessedObjectRef(
            object_type=AssessedObjectType.WORK_ACTIVITY,
            reference="Hot work",
        ),
        assessor_id=UserId(value=uuid4()),
        assessment_date=now,
    )
    actor = UserId(value=uuid4())
    with pytest.raises(RiskAssessmentInherentRiskRequired):
        assessment.approve(at=now, approved_by=actor, expected_version=1)

    ready = assessment.update_details(
        at=now,
        expected_version=1,
        inherent_risk=assessment.build_evaluation(probability=2, severity=2),
        acceptance=RiskAcceptance(
            decision=RiskAcceptanceDecision.ACCEPTED,
            justification="Acceptable",
            reviewer_id=actor,
        ),
    )
    approved = ready.approve(at=now, approved_by=actor, expected_version=2)
    assert approved.status is RiskAssessmentStatus.APPROVED
    with pytest.raises(RiskAssessmentAlreadyApproved):
        approved.approve(at=now, approved_by=actor, expected_version=3)
