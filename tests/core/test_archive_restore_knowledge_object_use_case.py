from __future__ import annotations

from uuid import uuid4

from backend.core.application.commands.archive_knowledge_object import (
    ArchiveKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.restore_knowledge_object import (
    RestoreKnowledgeObjectCommand,
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
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_archive_and_restore_knowledge_object_preserves_history() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    archive_handler = ArchiveKnowledgeObjectHandler(unit_of_work)
    restore_handler = RestoreKnowledgeObjectHandler(unit_of_work)

    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
            payload={"name": "SafetyMAIN"},
        )
    )

    archived_object = archive_handler.handle(
        ArchiveKnowledgeObjectCommand(object_id=created_object.header.id)
    )
    restored_object = restore_handler.handle(
        RestoreKnowledgeObjectCommand(object_id=created_object.header.id)
    )

    history = tuple(unit_of_work.knowledge_objects.history(created_object.header.id))
    current_object = unit_of_work.knowledge_objects.get(created_object.header.id)

    assert archived_object.header.status is KnowledgeObjectStatus.ARCHIVED
    assert archived_object.header.version.value == 2
    assert restored_object.header.status is KnowledgeObjectStatus.ACTIVE
    assert restored_object.header.version.value == 3
    assert restored_object.payload == created_object.payload

    assert [item.header.version.value for item in history] == [1, 2]
    assert history[0].header.status is KnowledgeObjectStatus.DRAFT
    assert history[1].header.status is KnowledgeObjectStatus.ARCHIVED
    assert current_object == restored_object
