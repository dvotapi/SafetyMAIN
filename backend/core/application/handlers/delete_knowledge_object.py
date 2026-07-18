from __future__ import annotations

from backend.core.application.commands.delete_knowledge_object import (
    DeleteKnowledgeObjectCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.knowledge_object import KnowledgeObject
from backend.core.domain.services import KnowledgeObjectService


class DeleteKnowledgeObjectHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        service: KnowledgeObjectService | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._service = service or KnowledgeObjectService()

    def handle(self, command: DeleteKnowledgeObjectCommand) -> KnowledgeObject:
        current_object = self._unit_of_work.knowledge_objects.get(command.object_id)
        deleted_object, _event = self._service.delete(current_object)
        self._unit_of_work.knowledge_objects.update(deleted_object)
        self._unit_of_work.commit()

        return deleted_object
