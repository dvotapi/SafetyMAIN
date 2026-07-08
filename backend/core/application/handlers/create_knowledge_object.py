from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
)


class CreateKnowledgeObjectHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: CreateKnowledgeObjectCommand) -> KnowledgeObject:
        now = datetime.now(UTC)
        knowledge_object = KnowledgeObject(
            header=KnowledgeObjectHeader(
                id=uuid4(),
                object_type=command.object_type,
                organization_id=command.organization_id,
                status=command.status,
                version=1,
                created_at=now,
                updated_at=now,
            ),
            payload=command.payload,
        )

        saved_object = self._unit_of_work.knowledge_objects.save(knowledge_object)
        self._unit_of_work.commit()

        return saved_object
