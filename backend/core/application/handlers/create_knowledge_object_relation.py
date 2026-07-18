from __future__ import annotations

from backend.core.application.commands.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.services import KnowledgeObjectRelationService


class CreateKnowledgeObjectRelationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        service: KnowledgeObjectRelationService | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._service = service or KnowledgeObjectRelationService()

    def handle(
        self,
        command: CreateKnowledgeObjectRelationCommand,
    ) -> KnowledgeObjectRelation:
        source_object = self._unit_of_work.knowledge_objects.get(
            command.source_object_id
        )
        target_object = self._unit_of_work.knowledge_objects.get(
            command.target_object_id
        )
        relation, _event = self._service.create_relation(
            source_object=source_object,
            target_object=target_object,
            relation_type=command.relation_type,
        )

        self._unit_of_work.relations.add(relation)
        self._unit_of_work.commit()

        return relation
