from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObject,
    KnowledgeObjectNotFound,
    KnowledgeObjectVersionConflict,
)
from backend.core.domain.repositories import KnowledgeObjectRepositoryContract
from backend.core.domain.value_objects import KnowledgeObjectType, OrganizationId
from backend.core.domain.value_objects.knowledge_object_search_criteria import (
    KnowledgeObjectSearchCriteria,
)


class KnowledgeObjectRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> KnowledgeObjectRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_empty_history(
        self,
        repository: KnowledgeObjectRepositoryContract,
    ) -> None:
        knowledge_object = create_knowledge_object()

        repository.add(knowledge_object)

        assert repository.get(knowledge_object.header.id) == knowledge_object
        assert repository.history(knowledge_object.header.id) == ()

    def test_duplicate_and_missing_object_errors(
        self,
        repository: KnowledgeObjectRepositoryContract,
    ) -> None:
        knowledge_object = create_knowledge_object()
        repository.add(knowledge_object)

        with pytest.raises(DuplicateKnowledgeObject):
            repository.add(knowledge_object)
        with pytest.raises(KnowledgeObjectNotFound):
            repository.get(create_knowledge_object().header.id)

    def test_valid_update_and_ordered_history(
        self,
        repository: KnowledgeObjectRepositoryContract,
    ) -> None:
        version_1 = create_knowledge_object(status=KnowledgeObjectStatus.ACTIVE)
        repository.add(version_1)
        version_2 = next_version(version_1, status=KnowledgeObjectStatus.ARCHIVED)
        repository.update(version_2)
        version_3 = next_version(version_2, status=KnowledgeObjectStatus.DELETED)
        repository.update(version_3)

        history = repository.history(version_1.header.id)

        assert repository.get(version_1.header.id) == version_3
        assert history == (version_1, version_2)
        with pytest.raises(AttributeError):
            history.append(version_3)  # type: ignore[attr-defined]

    def test_invalid_stale_and_missing_update_errors(
        self,
        repository: KnowledgeObjectRepositoryContract,
    ) -> None:
        version_1 = create_knowledge_object()
        repository.add(version_1)

        with pytest.raises(KnowledgeObjectVersionConflict):
            repository.update(next_version(version_1, version=3))
        with pytest.raises(KnowledgeObjectVersionConflict):
            repository.update(version_1)
        with pytest.raises(KnowledgeObjectNotFound):
            repository.update(create_knowledge_object(version=2))
        assert repository.history(version_1.header.id) == ()

    def test_missing_history_raises_not_found(
        self,
        repository: KnowledgeObjectRepositoryContract,
    ) -> None:
        with pytest.raises(KnowledgeObjectNotFound):
            repository.history(create_knowledge_object().header.id)

    def test_search_contract(
        self,
        repository: KnowledgeObjectRepositoryContract,
    ) -> None:
        organization_id = OrganizationId(value=uuid4())
        other_organization_id = OrganizationId(value=uuid4())
        now = datetime.now(UTC)
        first = create_knowledge_object(
            object_id=UUID("00000000-0000-0000-0000-000000000001"),
            organization_id=organization_id,
            object_type="Instruction",
            status=KnowledgeObjectStatus.ACTIVE,
            created_at=now,
            payload={"department": "production", "approved": True, "risk_level": 3},
        )
        second = create_knowledge_object(
            object_id=UUID("00000000-0000-0000-0000-000000000002"),
            organization_id=organization_id,
            object_type="Instruction",
            status=KnowledgeObjectStatus.ARCHIVED,
            created_at=now + timedelta(seconds=1),
            payload={"department": "production", "approved": True, "risk_level": 3},
        )
        deleted = create_knowledge_object(
            organization_id=organization_id,
            object_type="Instruction",
            status=KnowledgeObjectStatus.DELETED,
            payload={"department": "production", "approved": True},
        )
        for item in (
            first,
            second,
            deleted,
            create_knowledge_object(organization_id=other_organization_id),
            create_knowledge_object(
                organization_id=organization_id,
                object_type="Risk",
                payload={"department": "production", "approved": True},
            ),
        ):
            repository.add(item)

        result = repository.search(
            KnowledgeObjectSearchCriteria(
                organization_id=organization_id,
                object_type=KnowledgeObjectType(value="instruction"),
                metadata_equals={
                    "department": "production",
                    "approved": True,
                    "risk_level": 3,
                },
                limit=1,
                offset=1,
            )
        )
        deleted_result = repository.search(
            KnowledgeObjectSearchCriteria(
                organization_id=organization_id,
                status=KnowledgeObjectStatus.DELETED,
                limit=100,
                offset=0,
            )
        )
        type_sensitive_result = repository.search(
            KnowledgeObjectSearchCriteria(
                organization_id=organization_id,
                metadata_equals={"approved": 1},
                limit=100,
                offset=0,
            )
        )
        empty_result = repository.search(
            KnowledgeObjectSearchCriteria(
                organization_id=organization_id,
                metadata_equals={"missing": "value"},
                limit=100,
                offset=0,
            )
        )

        assert result.items == (second,)
        assert result.total == 2
        assert deleted_result.items == (deleted,)
        assert type_sensitive_result.items == ()
        assert empty_result.items == ()
        with pytest.raises(AttributeError):
            empty_result.items.append(first)  # type: ignore[attr-defined]


def create_knowledge_object(
    *,
    object_id: UUID | None = None,
    organization_id: OrganizationId | None = None,
    object_type: str = "Object",
    status: KnowledgeObjectStatus = KnowledgeObjectStatus.ACTIVE,
    version: int = 1,
    created_at: datetime | None = None,
    payload: dict[str, object] | None = None,
) -> KnowledgeObject:
    now = created_at or datetime.now(UTC)
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=object_id or uuid4(),
            object_type=object_type,
            organization_id=organization_id or uuid4(),
            status=status,
            version=version,
            created_at=now,
            updated_at=now,
        ),
        payload=payload or {},
    )


def next_version(
    knowledge_object: KnowledgeObject,
    *,
    status: KnowledgeObjectStatus | None = None,
    version: int | None = None,
    payload: dict[str, object] | None = None,
) -> KnowledgeObject:
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=knowledge_object.header.id,
            object_type=knowledge_object.header.object_type,
            organization_id=knowledge_object.header.organization_id,
            status=status or knowledge_object.header.status,
            version=version or knowledge_object.header.version.value + 1,
            created_at=knowledge_object.header.created_at,
            updated_at=datetime.now(UTC),
        ),
        payload=payload or knowledge_object.payload,
    )


def assert_invalid_search_criteria_rejected() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObjectSearchCriteria(
            organization_id=OrganizationId(value=uuid4()),
            limit=0,
            offset=0,
        )
