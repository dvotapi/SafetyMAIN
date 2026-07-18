from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import KnowledgeObjectNotFound
from backend.core.domain.services import KnowledgeObjectService
from backend.core.domain.value_objects import KnowledgeObjectId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
)


def _create_knowledge_object() -> KnowledgeObject:
    now = datetime.now(UTC)
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Organization",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.DRAFT,
            version=1,
            created_at=now,
            updated_at=now,
        ),
        payload={"name": "SafetyMAIN"},
    )


def test_repository_get_returns_current_version_or_raises() -> None:
    repository = InMemoryKnowledgeObjectRepository()
    knowledge_object = _create_knowledge_object()

    repository.add(knowledge_object)

    assert repository.get(knowledge_object.header.id) == knowledge_object

    with pytest.raises(KnowledgeObjectNotFound):
        repository.get(KnowledgeObjectId(value=uuid4()))


def test_repository_add_and_update_return_none() -> None:
    repository = InMemoryKnowledgeObjectRepository()
    service = KnowledgeObjectService()
    knowledge_object = _create_knowledge_object()

    add_result = repository.add(knowledge_object)
    updated_object, _event = service.create_next_version(
        knowledge_object,
        status=KnowledgeObjectStatus.ACTIVE,
        payload={"name": "Updated"},
    )
    update_result = repository.update(updated_object)

    assert add_result is None
    assert update_result is None
    assert repository.get(knowledge_object.header.id) == updated_object


def test_repository_history_is_oldest_to_newest_previous_versions_only() -> None:
    repository = InMemoryKnowledgeObjectRepository()
    service = KnowledgeObjectService()
    version_1 = _create_knowledge_object()
    repository.add(version_1)

    version_2, _event = service.create_next_version(
        version_1,
        status=KnowledgeObjectStatus.ACTIVE,
        payload={"name": "Version 2"},
    )
    repository.update(version_2)
    version_3, _event = service.create_next_version(
        version_2,
        status=KnowledgeObjectStatus.ARCHIVED,
        payload={"name": "Version 3"},
    )
    repository.update(version_3)

    history = repository.history(version_1.header.id)

    assert [item.header.version.value for item in history] == [1, 2]
    assert repository.get(version_1.header.id) == version_3


def test_repository_history_result_cannot_mutate_repository_state() -> None:
    repository = InMemoryKnowledgeObjectRepository()
    service = KnowledgeObjectService()
    version_1 = _create_knowledge_object()
    repository.add(version_1)
    version_2, _event = service.create_next_version(
        version_1,
        status=KnowledgeObjectStatus.ACTIVE,
    )
    repository.update(version_2)

    history = repository.history(version_1.header.id)

    with pytest.raises(AttributeError):
        history.append(version_2)  # type: ignore[attr-defined]

    assert [item.header.version.value for item in repository.history(version_1.header.id)] == [
        1
    ]


def test_repository_history_raises_for_missing_object() -> None:
    repository = InMemoryKnowledgeObjectRepository()

    with pytest.raises(KnowledgeObjectNotFound):
        repository.history(KnowledgeObjectId(value=uuid4()))


def test_unit_of_work_context_manager_returns_self() -> None:
    unit_of_work = InMemoryUnitOfWork()

    with unit_of_work as active_unit_of_work:
        assert active_unit_of_work is unit_of_work

    assert unit_of_work.rolled_back is True


def test_unit_of_work_context_manager_rolls_back_on_exception() -> None:
    unit_of_work = InMemoryUnitOfWork()

    with pytest.raises(RuntimeError):
        with unit_of_work:
            raise RuntimeError("boom")

    assert unit_of_work.rolled_back is True
