from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.commands.archive_knowledge_object import (
    ArchiveKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.restore_knowledge_object import (
    RestoreKnowledgeObjectCommand,
)
from backend.core.application.commands.update_knowledge_object import (
    UpdateKnowledgeObjectCommand,
)
from backend.core.application.handlers.archive_knowledge_object import (
    ArchiveKnowledgeObjectHandler,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.application.handlers.restore_knowledge_object import (
    RestoreKnowledgeObjectHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObject,
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectAlreadyActive,
    KnowledgeObjectAlreadyArchived,
    KnowledgeObjectNotFound,
    KnowledgeObjectVersionConflict,
    SafetyMainDomainError,
)
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectVersion,
    OrganizationId,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
)


def test_missing_object_raises_typed_domain_exception() -> None:
    missing_id = KnowledgeObjectId(value=uuid4())
    handler = UpdateKnowledgeObjectHandler(InMemoryUnitOfWork())

    with pytest.raises(KnowledgeObjectNotFound) as exc_info:
        handler.handle(
            UpdateKnowledgeObjectCommand(
                object_id=missing_id,
                organization_id=OrganizationId(value=uuid4()),
                expected_version=KnowledgeObjectVersion(value=1),
                status=KnowledgeObjectStatus.ACTIVE,
                payload={},
            )
        )

    assert isinstance(exc_info.value, SafetyMainDomainError)
    assert exc_info.value.knowledge_object_id == missing_id
    assert str(missing_id.value) in str(exc_info.value)


def test_archive_already_archived_object_fails() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    archive_handler = ArchiveKnowledgeObjectHandler(unit_of_work)
    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
            payload={"name": "SafetyMAIN"},
        )
    )
    archived_object = archive_handler.handle(
        ArchiveKnowledgeObjectCommand(
            object_id=created_object.header.id,
            organization_id=created_object.header.organization_id,
        )
    )

    with pytest.raises(KnowledgeObjectAlreadyArchived) as exc_info:
        archive_handler.handle(
            ArchiveKnowledgeObjectCommand(
                object_id=archived_object.header.id,
                organization_id=archived_object.header.organization_id,
            )
        )

    assert exc_info.value.knowledge_object_id == archived_object.header.id
    assert "already archived" in str(exc_info.value)


def test_restore_active_object_fails() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    restore_handler = RestoreKnowledgeObjectHandler(unit_of_work)
    active_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.ACTIVE,
            payload={"name": "SafetyMAIN"},
        )
    )

    with pytest.raises(KnowledgeObjectAlreadyActive) as exc_info:
        restore_handler.handle(
            RestoreKnowledgeObjectCommand(
                object_id=active_object.header.id,
                organization_id=active_object.header.organization_id,
            )
        )

    assert exc_info.value.knowledge_object_id == active_object.header.id
    assert "already active" in str(exc_info.value)


def test_duplicate_knowledge_object_fails() -> None:
    now = datetime.now(UTC)
    repository = InMemoryKnowledgeObjectRepository()
    knowledge_object = KnowledgeObject(
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

    repository.add(knowledge_object)

    with pytest.raises(DuplicateKnowledgeObject) as exc_info:
        repository.add(knowledge_object)

    assert exc_info.value.knowledge_object_id == knowledge_object.header.id
    assert "already exists" in str(exc_info.value)


def test_invalid_state_transition_preserves_context() -> None:
    knowledge_object_id = KnowledgeObjectId(value=uuid4())

    error = InvalidKnowledgeObjectStateTransition(
        knowledge_object_id=knowledge_object_id,
        current_status=KnowledgeObjectStatus.DELETED,
        requested_status=KnowledgeObjectStatus.ACTIVE,
    )

    assert error.knowledge_object_id == knowledge_object_id
    assert error.current_status is KnowledgeObjectStatus.DELETED
    assert error.requested_status is KnowledgeObjectStatus.ACTIVE
    assert "Invalid Knowledge Object state transition" in str(error)


def test_version_conflict_preserves_context() -> None:
    knowledge_object_id = KnowledgeObjectId(value=uuid4())
    expected_version = KnowledgeObjectVersion(value=2)
    actual_version = KnowledgeObjectVersion(value=3)

    error = KnowledgeObjectVersionConflict(
        knowledge_object_id=knowledge_object_id,
        expected_version=expected_version,
        actual_version=actual_version,
    )

    assert error.knowledge_object_id == knowledge_object_id
    assert error.expected_version == expected_version
    assert error.actual_version == actual_version
    assert "version conflict" in str(error)
