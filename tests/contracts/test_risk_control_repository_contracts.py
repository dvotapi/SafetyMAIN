from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_control import (
    DuplicateRiskControlCode,
    RiskControlVersionConflict,
)
from backend.core.domain.repositories.risk_control_repository import (
    RiskControlRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_control_components import (
    ControlReviewSchedule,
    EvidenceReference,
)
from backend.core.domain.value_objects.risk_control_query import RiskControlQuery
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlType,
    EffectivenessResult,
    EvidenceType,
    RiskControlStatus,
)
from backend.core.domain.value_objects.safety_ids import RiskAssessmentId
from backend.core.infrastructure.persistence.in_memory.risk_control_repository import (
    InMemoryRiskControlRepository,
)
from tests.fixtures.risk_controls import (
    advance_to_implemented,
    assert_control_domain_equal,
    make_owner,
    risk_control_draft,
    risk_control_rich_round_trip,
)


def _create(*, organization_id=None, code="RC-001") -> RiskControl:
    return risk_control_draft(organization_id=organization_id, code=code)


class RiskControlRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> RiskControlRepositoryContract:
        raise NotImplementedError

    def test_add_get_isolation_and_duplicate(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        control = _create()
        repository.add(control)
        loaded = repository.get(control.organization_id, control.id)
        assert loaded is not None
        assert_control_domain_equal(loaded, control)
        assert repository.get(OrganizationId(value=uuid4()), control.id) is None
        with pytest.raises(DuplicateRiskControlCode):
            repository.add(
                _create(
                    organization_id=control.organization_id,
                    code=control.code.value,
                )
            )

    def test_list_filters_pagination_and_version_conflict(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        org = OrganizationId(value=uuid4())
        first = _create(organization_id=org, code="RC-A")
        second = _create(organization_id=org, code="RC-B")
        other = _create(code="RC-C")
        repository.add(first)
        repository.add(second)
        repository.add(other)

        page = repository.list(
            RiskControlQuery(
                organization_id=org,
                status=RiskControlStatus.DRAFT,
                hierarchy_level=ControlType.ENGINEERING,
                control_nature=ControlNature.PREVENTIVE,
                owner_reference=first.owner.owner_reference if first.owner else None,
                search="guard",
                limit=1,
                offset=0,
            )
        )
        assert page.total == 2
        assert len(page.items) == 1

        empty = repository.list(
            RiskControlQuery(
                organization_id=org,
                status=RiskControlStatus.IMPLEMENTED,
            )
        )
        assert empty.total == 0

        updated = first.update_details(
            at=datetime.now(UTC),
            actor_id=first.created_by,
            expected_version=1,
            title="Updated",
        )
        repository.save(updated, expected_version=1)
        with pytest.raises(RiskControlVersionConflict):
            repository.save(updated, expected_version=1)
        reloaded = repository.get(org, first.id)
        assert reloaded is not None
        assert reloaded.title == "Updated"
        assert reloaded.version == 2

    def test_source_uniqueness_and_exists_for_source(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        org = OrganizationId(value=uuid4())
        assessment_id = RiskAssessmentId(value=uuid4())
        control = risk_control_draft(
            organization_id=org,
            risk_assessment_id=assessment_id,
            source_control_reference="ctrl-1",
            code="RC-SRC-1",
        )
        repository.add(control)
        assert repository.exists_for_source(org, assessment_id, "ctrl-1") is True
        assert repository.exists_for_source(org, assessment_id, "ctrl-2") is False
        assert (
            repository.exists_for_source(
                OrganizationId(value=uuid4()),
                assessment_id,
                "ctrl-1",
            )
            is False
        )
        duplicate = risk_control_draft(
            organization_id=org,
            risk_assessment_id=assessment_id,
            source_control_reference="ctrl-1",
            code="RC-SRC-2",
        )
        with pytest.raises(DuplicateRiskControlCode):
            repository.add(duplicate)

    def test_rich_round_trip_preserves_nested_state(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        control = risk_control_rich_round_trip()
        repository.add(control)
        loaded = repository.get(control.organization_id, control.id)
        assert loaded is not None
        assert_control_domain_equal(loaded, control)
        assert loaded.lifecycle_status is RiskControlStatus.VERIFIED_EFFECTIVE
        assert loaded.latest_effectiveness_result is EffectivenessResult.EFFECTIVE
        assert len(loaded.verifications) == 1
        assert len(loaded.evidence) == 1
        assert len(loaded.implementation.milestones) == 2
        assert loaded.extension_data["country_profile"] == "ru"
        assert loaded.source.source_type.value == "management_decision"

    def test_optimistic_concurrency_across_mutation_categories(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        now = datetime.now(UTC)
        control = risk_control_draft()
        repository.add(control)
        actor = control.created_by

        a = repository.get(control.organization_id, control.id)
        b = repository.get(control.organization_id, control.id)
        assert a is not None and b is not None

        a_owner = a.assign_owner(
            owner=make_owner(actor=actor, at=now, reference="new-owner"),
            at=now,
            actor_id=actor,
            expected_version=1,
            reason="reassign",
        )
        repository.save(a_owner, expected_version=1)

        with pytest.raises(RiskControlVersionConflict):
            repository.save(
                b.update_details(
                    at=now,
                    actor_id=actor,
                    expected_version=1,
                    title="stale",
                ),
                expected_version=1,
            )
        reloaded = repository.get(control.organization_id, control.id)
        assert reloaded is not None
        assert reloaded.owner is not None
        assert reloaded.owner.owner_reference == "new-owner"
        assert reloaded.title != "stale"
        assert reloaded.version == 2

        # progress / evidence / verification / review stale writes
        implemented = advance_to_implemented(reloaded, actor=actor, at=now)
        repository.save(implemented, expected_version=reloaded.version)
        base = repository.get(control.organization_id, control.id)
        assert base is not None
        stale = repository.get(control.organization_id, control.id)
        assert stale is not None
        reviewed = base.schedule_review(
            schedule=ControlReviewSchedule(
                review_required=True,
                review_frequency_days=30,
                next_review_date=now + timedelta(days=30),
            ),
            at=now,
            actor_id=actor,
            expected_version=base.version,
        )
        repository.save(reviewed, expected_version=base.version)
        with pytest.raises(RiskControlVersionConflict):
            repository.save(
                stale.add_evidence(
                    evidence=EvidenceReference(
                        evidence_type=EvidenceType.OTHER,
                        external_reference="doc://stale",
                        title="Stale",
                        captured_at=now,
                        captured_by=actor,
                    ),
                    at=now,
                    actor_id=actor,
                    expected_version=stale.version,
                    allow_after_implemented=True,
                ),
                expected_version=stale.version,
            )
        final = repository.get(control.organization_id, control.id)
        assert final is not None
        assert final.next_review_date == now + timedelta(days=30)
        assert all(item.external_reference != "doc://stale" for item in final.evidence)

    def test_overdue_filter_uses_as_of(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        now = datetime.now(UTC)
        control = risk_control_draft()
        scheduled = control.schedule_review(
            schedule=ControlReviewSchedule(
                review_required=True,
                next_review_date=now - timedelta(days=1),
                review_frequency_days=30,
            ),
            at=now,
            actor_id=control.created_by,
            expected_version=1,
        )
        repository.add(scheduled)
        page = repository.list(
            RiskControlQuery(
                organization_id=control.organization_id,
                overdue_only=True,
                as_of=now,
            )
        )
        assert page.total == 1
        not_yet = repository.list(
            RiskControlQuery(
                organization_id=control.organization_id,
                overdue_only=True,
                as_of=now - timedelta(days=2),
            )
        )
        assert not_yet.total == 0

    def test_awaiting_verification_filter(
        self, repository: RiskControlRepositoryContract
    ) -> None:
        now = datetime.now(UTC)
        control = risk_control_draft()
        repository.add(control)
        implemented = advance_to_implemented(
            control, actor=control.created_by, at=now
        )
        repository.save(implemented, expected_version=1)
        page = repository.list(
            RiskControlQuery(
                organization_id=control.organization_id,
                awaiting_verification=True,
            )
        )
        assert page.total == 1
        assert page.items[0].lifecycle_status is RiskControlStatus.IMPLEMENTED


class TestInMemoryRiskControlRepository(RiskControlRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> RiskControlRepositoryContract:
        return InMemoryRiskControlRepository()
