from __future__ import annotations

from backend.core.application.commands.update_knowledge_object import (
    UpdateKnowledgeObjectCommand,
)
from backend.core.application.handlers.knowledge_object_access import (
    validate_knowledge_object_organization,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.knowledge_object import KnowledgeObject, KnowledgeObjectStatus
from backend.core.domain.exceptions import (
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectVersionConflict,
)
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
        validate_knowledge_object_organization(current_object, command.organization_id)

        if current_object.header.version.value != command.expected_version.value:
            raise KnowledgeObjectVersionConflict(
                knowledge_object_id=command.object_id,
                expected_version=command.expected_version,
                actual_version=current_object.header.version,
            )

        if current_object.header.status is KnowledgeObjectStatus.DELETED:
            raise InvalidKnowledgeObjectStateTransition(
                knowledge_object_id=command.object_id,
                current_status=current_object.header.status,
                requested_status=current_object.header.status,
            )

        next_status = (
            command.status
            if command.status is not None
            else current_object.header.status
        )
        updated_object, _event = self._service.create_next_version(
            current_object,
            status=next_status,
            payload=command.payload,
        )

        self._unit_of_work.knowledge_objects.update(updated_object)
        self._unit_of_work.commit()

        return updated_object
