from __future__ import annotations

from uuid import uuid4

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.update_knowledge_object import (
    UpdateKnowledgeObjectCommand,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_update_knowledge_object_creates_new_version_and_preserves_history() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    update_handler = UpdateKnowledgeObjectHandler(unit_of_work)

    created_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Organization",
            organization_id=uuid4(),
            payload={"name": "SafetyMAIN"},
        )
    )

    updated_object = update_handler.handle(
        UpdateKnowledgeObjectCommand(
            object_id=created_object.header.id,
            status=KnowledgeObjectStatus.ACTIVE,
            payload={"name": "SafetyMAIN Updated"},
        )
    )

    history = tuple(unit_of_work.knowledge_objects.history(created_object.header.id))
    current_object = unit_of_work.knowledge_objects.get(created_object.header.id)

    assert updated_object.header.id == created_object.header.id
    assert updated_object.header.object_type == created_object.header.object_type
    assert updated_object.header.organization_id == created_object.header.organization_id
    assert updated_object.header.version.value == 2
    assert updated_object.header.status is KnowledgeObjectStatus.ACTIVE
    assert updated_object.payload == {"name": "SafetyMAIN Updated"}

    assert len(history) == 1
    assert history[0].header.version.value == 1
    assert history[0].payload == {"name": "SafetyMAIN"}
    assert current_object == updated_object
