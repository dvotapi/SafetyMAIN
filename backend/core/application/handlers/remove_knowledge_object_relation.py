from __future__ import annotations

from backend.core.application.commands.remove_knowledge_object_relation import (
    RemoveKnowledgeObjectRelationCommand,
)
from backend.core.application.handlers.knowledge_object_access import (
    validate_knowledge_object_relation_organization,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.services import KnowledgeObjectRelationService


class RemoveKnowledgeObjectRelationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        service: KnowledgeObjectRelationService | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._service = service or KnowledgeObjectRelationService()

    def handle(self, command: RemoveKnowledgeObjectRelationCommand) -> None:
        relation = self._unit_of_work.relations.get(command.relation_id)
        validate_knowledge_object_relation_organization(relation, command.organization_id)
        _event = self._service.remove_relation(relation)
        self._unit_of_work.relations.remove(command.relation_id)
        self._unit_of_work.commit()
