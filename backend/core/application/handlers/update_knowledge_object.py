from __future__ import annotations

from backend.core.application.commands.update_knowledge_object import (
    UpdateKnowledgeObjectCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.knowledge_object import KnowledgeObject
from backend.core.domain.services import KnowledgeObjectService


class UpdateKnowledgeObjectHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        service: KnowledgeObjectService | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._service = service or KnowledgeObjectService()

    def handle(self, command: UpdateKnowledgeObjectCommand) -> KnowledgeObject:
        current_object = self._unit_of_work.knowledge_objects.get(command.object_id)

        if current_object is None:
            raise LookupError(f"Knowledge Object not found: {command.object_id}")

        updated_object = self._service.create_next_version(
            current_object,
            status=command.status,
            payload=command.payload,
        )

        saved_object = self._unit_of_work.knowledge_objects.update(updated_object)
        self._unit_of_work.commit()

        return saved_object
