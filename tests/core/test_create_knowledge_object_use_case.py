from __future__ import annotations

from uuid import uuid4

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_create_knowledge_object_use_case() -> None:
    organization_id = uuid4()
    unit_of_work = InMemoryUnitOfWork()
    handler = CreateKnowledgeObjectHandler(unit_of_work)
    command = CreateKnowledgeObjectCommand(
        object_type="Organization",
        organization_id=organization_id,
        payload={"name": "SafetyMAIN"},
    )

    knowledge_object = handler.handle(command)
    stored_object = unit_of_work.knowledge_objects.get(knowledge_object.header.id)

    assert knowledge_object.header.object_type.value == "organization"
    assert knowledge_object.header.organization_id.value == organization_id
    assert knowledge_object.header.status is KnowledgeObjectStatus.DRAFT
    assert knowledge_object.header.version.value == 1
    assert knowledge_object.payload == {"name": "SafetyMAIN"}
    assert stored_object == knowledge_object
    assert unit_of_work.committed is True
    assert unit_of_work.rolled_back is False
