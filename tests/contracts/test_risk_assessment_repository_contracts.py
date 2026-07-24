from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import (
    DuplicateRiskAssessmentCode,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.repositories.risk_assessment_repository import (
    RiskAssessmentRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
    RiskAcceptance,
)
from backend.core.domain.value_objects.risk_assessment_query import RiskAssessmentQuery
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    RiskAcceptanceDecision,
    RiskAssessmentStatus,
)
from backend.core.domain.value_objects.safety_ids import HazardId
from backend.core.infrastructure.persistence.in_memory.risk_assessment_repository import (
    InMemoryRiskAssessmentRepository,
)


def _create(
    *,
    organization_id: OrganizationId | None = None,
    hazard_id: HazardId | None = None,
    code: str = "RA-001",
    profile: AssessmentProfileCode = AssessmentProfileCode.SIMPLE_5X5,
    reference: str = "Bay-1",
    created_at: datetime | None = None,
) -> RiskAssessment:
    now = created_at or datetime.now(UTC)
    return RiskAssessment.create(
        organization_id=organization_id or OrganizationId(value=uuid4()),
        hazard_id=hazard_id or HazardId(value=uuid4()),
        code=code,
        title="Conveyor residual risk",
        assessment_profile=profile,
        assessed_object=AssessedObjectRef(
            object_type=AssessedObjectType.WORKPLACE,
            reference=reference,
        ),
        assessor_id=UserId(value=uuid4()),
        assessment_date=now,
        created_at=now,
    )


class RiskAssessmentRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> RiskAssessmentRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_isolation(
        self,
        repository: RiskAssessmentRepositoryContract,
    ) -> None:
        assessment = _create()
        repository.add(assessment)
        assert repository.get(assessment.organization_id, assessment.id) == assessment
        assert (
            repository.get_by_code(assessment.organization_id, assessment.code)
            == assessment
        )
        assert repository.get(OrganizationId(value=uuid4()), assessment.id) is None

    def test_duplicate_code_and_list_filters(
        self,
        repository: RiskAssessmentRepositoryContract,
    ) -> None:
        org = OrganizationId(value=uuid4())
        hazard = HazardId(value=uuid4())
        first = _create(organization_id=org, hazard_id=hazard, code="RA-A")
        second = _create(
            organization_id=org,
            hazard_id=hazard,
            code="RA-B",
            created_at=datetime.now(UTC) - timedelta(days=1),
        )
        repository.add(first)
        repository.add(second)
        with pytest.raises(DuplicateRiskAssessmentCode):
            repository.add(_create(organization_id=org, code="RA-A"))

        page = repository.list(
            RiskAssessmentQuery(organization_id=org, hazard_id=hazard, offset=0, limit=10)
        )
        assert page.total == 2
        assert page.items[0].code.value == "RA-A"

    def test_approved_scope_and_concurrency(
        self,
        repository: RiskAssessmentRepositoryContract,
    ) -> None:
        assessment = _create()
        repository.add(assessment)
        actor = UserId(value=uuid4())
        with_inherent = assessment.update_details(
            at=datetime.now(UTC),
            expected_version=1,
            inherent_risk=assessment.build_evaluation(
                probability=3,
                severity=3,
                explanation="P3 S3",
            ),
            acceptance=RiskAcceptance(
                decision=RiskAcceptanceDecision.ACCEPTED,
                justification="Within tolerance",
                reviewer_id=actor,
            ),
        )
        repository.save(with_inherent, expected_version=1)
        approved = with_inherent.approve(
            at=datetime.now(UTC),
            approved_by=actor,
            expected_version=2,
        )
        repository.save(approved, expected_version=2)
        scoped = repository.list_approved_for_scope(
            organization_id=approved.organization_id,
            hazard_id=approved.hazard_id,
            assessment_profile=approved.assessment_profile,
            assessed_object=approved.assessed_object,
        )
        assert len(scoped) == 1
        assert scoped[0].status is RiskAssessmentStatus.APPROVED

        with pytest.raises(RiskAssessmentVersionConflict):
            repository.save(approved, expected_version=1)


class TestInMemoryRiskAssessmentRepositoryContract(RiskAssessmentRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> RiskAssessmentRepositoryContract:
        return InMemoryRiskAssessmentRepository()
