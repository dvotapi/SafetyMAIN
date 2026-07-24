from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.exceptions.hazard import (
    DuplicateHazardCode,
    HazardVersionConflict,
)
from backend.core.domain.repositories.hazard_repository import HazardRepositoryContract
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.hazard_query import HazardQuery
from backend.core.domain.value_objects.safety_enums import (
    AffectedSubject,
    HazardCategory,
    HazardSource,
    HazardStatus,
    SafetyDirection,
)
from backend.core.infrastructure.persistence.in_memory.hazard_repository import (
    InMemoryHazardRepository,
)


def _create_hazard(
    *,
    organization_id: OrganizationId | None = None,
    code: str = "HZ-001",
    status: HazardStatus = HazardStatus.DRAFT,
    category: HazardCategory = HazardCategory.PHYSICAL,
    created_at: datetime | None = None,
) -> Hazard:
    now = created_at or datetime.now(UTC)
    actor = UserId(value=uuid4())
    hazard = Hazard.create(
        organization_id=organization_id or OrganizationId(value=uuid4()),
        code=code,
        title="Fuel spill risk",
        description="Possible fuel spill near loading bay",
        category=category,
        safety_directions=(
            SafetyDirection.ENVIRONMENTAL_SAFETY,
            SafetyDirection.FIRE_SAFETY,
        ),
        source=HazardSource.INSPECTION,
        affected_subjects=(AffectedSubject.EMPLOYEE, AffectedSubject.ENVIRONMENT),
        identified_at=now,
        identified_by=actor,
        created_at=now,
    )
    if status is HazardStatus.ACTIVE:
        return hazard.activate(at=now + timedelta(seconds=1), reviewed_by=actor)
    if status is HazardStatus.ARCHIVED:
        return hazard.archive(
            at=now + timedelta(seconds=1),
            archived_by=actor,
            reason="Retired",
        )
    return hazard


class HazardRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> HazardRepositoryContract:
        raise NotImplementedError

    def test_add_and_get_by_id_and_code(
        self,
        repository: HazardRepositoryContract,
    ) -> None:
        hazard = _create_hazard()
        repository.add(hazard)

        loaded = repository.get(hazard.organization_id, hazard.id)
        assert loaded == hazard
        assert repository.get_by_code(hazard.organization_id, hazard.code) == hazard
        other_org = OrganizationId(value=uuid4())
        assert repository.get(other_org, hazard.id) is None

    def test_organization_isolation_and_duplicate_code(
        self,
        repository: HazardRepositoryContract,
    ) -> None:
        org_a = OrganizationId(value=uuid4())
        org_b = OrganizationId(value=uuid4())
        first = _create_hazard(organization_id=org_a, code="SHARED")
        second = _create_hazard(organization_id=org_b, code="SHARED")
        repository.add(first)
        repository.add(second)

        with pytest.raises(DuplicateHazardCode):
            repository.add(_create_hazard(organization_id=org_a, code="SHARED"))

        assert repository.get(org_a, second.id) is None

    def test_list_filters_archived_and_classifications(
        self,
        repository: HazardRepositoryContract,
    ) -> None:
        org = OrganizationId(value=uuid4())
        now = datetime.now(UTC)
        draft = _create_hazard(organization_id=org, code="D1", created_at=now)
        archived = _create_hazard(
            organization_id=org,
            code="A1",
            status=HazardStatus.ARCHIVED,
            created_at=now - timedelta(seconds=1),
        )
        repository.add(draft)
        repository.add(archived)

        default_page = repository.list(
            HazardQuery(organization_id=org, offset=0, limit=10)
        )
        assert default_page.total == 1
        assert default_page.items[0].id == draft.id

        with_archived = repository.list(
            HazardQuery(
                organization_id=org,
                include_archived=True,
                offset=0,
                limit=10,
            )
        )
        assert with_archived.total == 2

        filtered = repository.list(
            HazardQuery(
                organization_id=org,
                safety_direction=SafetyDirection.FIRE_SAFETY,
                category=HazardCategory.PHYSICAL,
                source=HazardSource.INSPECTION,
                affected_subject=AffectedSubject.EMPLOYEE,
                search="fuel",
                offset=0,
                limit=10,
            )
        )
        assert filtered.total == 1
        assert filtered.items[0].code.value == "D1"

    def test_pagination_and_deterministic_ordering(
        self,
        repository: HazardRepositoryContract,
    ) -> None:
        org = OrganizationId(value=uuid4())
        base = datetime.now(UTC)
        older = _create_hazard(
            organization_id=org,
            code="OLD",
            created_at=base - timedelta(days=1),
        )
        newer = _create_hazard(
            organization_id=org,
            code="NEW",
            created_at=base,
        )
        repository.add(older)
        repository.add(newer)

        page = repository.list(HazardQuery(organization_id=org, offset=0, limit=1))
        assert page.total == 2
        assert page.items[0].code.value == "NEW"

        page2 = repository.list(HazardQuery(organization_id=org, offset=1, limit=1))
        assert page2.items[0].code.value == "OLD"

    def test_optimistic_concurrency_and_lifecycle_persistence(
        self,
        repository: HazardRepositoryContract,
    ) -> None:
        hazard = _create_hazard()
        repository.add(hazard)
        actor = UserId(value=uuid4())
        activated = hazard.activate(at=datetime.now(UTC), reviewed_by=actor)
        repository.save(activated, expected_version=hazard.version)
        loaded = repository.get(hazard.organization_id, hazard.id)
        assert loaded is not None
        assert loaded.status is HazardStatus.ACTIVE
        assert loaded.version == 2

        with pytest.raises(HazardVersionConflict):
            repository.save(
                loaded.update_details(
                    at=datetime.now(UTC),
                    expected_version=1,
                    title="stale",
                ),
                expected_version=1,
            )


class TestInMemoryHazardRepositoryContract(HazardRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> HazardRepositoryContract:
        return InMemoryHazardRepository()
