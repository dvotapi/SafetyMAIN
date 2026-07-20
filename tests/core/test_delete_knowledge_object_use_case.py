from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.application.commands.archive_knowledge_object import (
    ArchiveKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.delete_knowledge_object import (
    DeleteKnowledgeObjectCommand,
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
from backend.core.application.handlers.delete_knowledge_object import (
    DeleteKnowledgeObjectHandler,
)
from backend.core.application.handlers.restore_knowledge_object import (
    RestoreKnowledgeObjectHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.exceptions import (
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectAlreadyDeleted,
)
from backend.core.domain.value_objects import KnowledgeObjectVersion
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_delete_knowledge_object_creates_deleted_version_and_preserves_history() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    delete_handler = DeleteKnowledgeObjectHandler(unit_of_work)
    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
            payload={"name": "SafetyMAIN"},
        )
    )

    deleted_object = delete_handler.handle(
        DeleteKnowledgeObjectCommand(
            object_id=created_object.header.id,
            organization_id=created_object.header.organization_id,
        )
    )
    history = unit_of_work.knowledge_objects.history(created_object.header.id)
    current_object = unit_of_work.knowledge_objects.get(created_object.header.id)

    assert deleted_object.header.status is KnowledgeObjectStatus.DELETED
    assert deleted_object.header.version.value == 2
    assert deleted_object.payload == created_object.payload
    assert [item.header.version.value for item in history] == [1]
    assert current_object == deleted_object


def test_deleting_already_deleted_object_fails() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    delete_handler = DeleteKnowledgeObjectHandler(unit_of_work)
    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
        )
    )
    deleted_object = delete_handler.handle(
        DeleteKnowledgeObjectCommand(
            object_id=created_object.header.id,
            organization_id=created_object.header.organization_id,
        )
    )

    with pytest.raises(KnowledgeObjectAlreadyDeleted) as exc_info:
        delete_handler.handle(
            DeleteKnowledgeObjectCommand(
                object_id=deleted_object.header.id,
                organization_id=deleted_object.header.organization_id,
            )
        )

    assert exc_info.value.knowledge_object_id == deleted_object.header.id


def test_update_after_delete_fails() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    delete_handler = DeleteKnowledgeObjectHandler(unit_of_work)
    update_handler = UpdateKnowledgeObjectHandler(unit_of_work)
    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
        )
    )
    deleted_object = delete_handler.handle(
        DeleteKnowledgeObjectCommand(
            object_id=created_object.header.id,
            organization_id=created_object.header.organization_id,
        )
    )

    with pytest.raises(InvalidKnowledgeObjectStateTransition) as exc_info:
        update_handler.handle(
            UpdateKnowledgeObjectCommand(
                object_id=deleted_object.header.id,
                organization_id=deleted_object.header.organization_id,
                expected_version=KnowledgeObjectVersion(
                    value=deleted_object.header.version.value
                ),
                status=KnowledgeObjectStatus.ACTIVE,
                payload={"name": "Updated"},
            )
        )

    assert exc_info.value.knowledge_object_id == deleted_object.header.id
    assert exc_info.value.current_status is KnowledgeObjectStatus.DELETED


def test_archive_after_delete_fails() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    delete_handler = DeleteKnowledgeObjectHandler(unit_of_work)
    archive_handler = ArchiveKnowledgeObjectHandler(unit_of_work)
    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
        )
    )
    deleted_object = delete_handler.handle(
        DeleteKnowledgeObjectCommand(
            object_id=created_object.header.id,
            organization_id=created_object.header.organization_id,
        )
    )

    with pytest.raises(InvalidKnowledgeObjectStateTransition) as exc_info:
        archive_handler.handle(
            ArchiveKnowledgeObjectCommand(
                object_id=deleted_object.header.id,
                organization_id=deleted_object.header.organization_id,
            )
        )

    assert exc_info.value.knowledge_object_id == deleted_object.header.id
    assert exc_info.value.current_status is KnowledgeObjectStatus.DELETED
    assert exc_info.value.requested_status is KnowledgeObjectStatus.ARCHIVED


def test_restore_after_delete_fails() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    delete_handler = DeleteKnowledgeObjectHandler(unit_of_work)
    restore_handler = RestoreKnowledgeObjectHandler(unit_of_work)
    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
        )
    )
    deleted_object = delete_handler.handle(
        DeleteKnowledgeObjectCommand(
            object_id=created_object.header.id,
            organization_id=created_object.header.organization_id,
        )
    )

    with pytest.raises(InvalidKnowledgeObjectStateTransition) as exc_info:
        restore_handler.handle(
            RestoreKnowledgeObjectCommand(
                object_id=deleted_object.header.id,
                organization_id=deleted_object.header.organization_id,
            )
        )

    assert exc_info.value.knowledge_object_id == deleted_object.header.id
    assert exc_info.value.current_status is KnowledgeObjectStatus.DELETED
    assert exc_info.value.requested_status is KnowledgeObjectStatus.ACTIVE
