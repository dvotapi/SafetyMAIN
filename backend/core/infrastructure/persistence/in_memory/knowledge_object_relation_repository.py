from __future__ import annotations

from typing import Sequence
from uuid import UUID

from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObjectRelation,
    KnowledgeObjectRelationNotFound,
)
from backend.core.domain.repositories import KnowledgeObjectRelationRepositoryContract
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


class InMemoryKnowledgeObjectRelationRepository(
    KnowledgeObjectRelationRepositoryContract
):
    def __init__(self) -> None:
        self._relations: dict[UUID, KnowledgeObjectRelation] = {}

    def add(self, relation: KnowledgeObjectRelation) -> None:
        if self.exists(
            organization_id=relation.organization_id,
            source_object_id=relation.source_object_id,
            target_object_id=relation.target_object_id,
            relation_type=relation.relation_type,
        ):
            raise DuplicateKnowledgeObjectRelation(
                organization_id=relation.organization_id,
                source_object_id=relation.source_object_id,
                target_object_id=relation.target_object_id,
                relation_type=relation.relation_type,
            )

        self._relations[relation.relation_id] = relation

    def get(self, relation_id: UUID) -> KnowledgeObjectRelation:
        try:
            return self._relations[relation_id]
        except KeyError as exc:
            raise KnowledgeObjectRelationNotFound(relation_id) from exc

    def remove(self, relation_id: UUID) -> None:
        if relation_id not in self._relations:
            raise KnowledgeObjectRelationNotFound(relation_id)

        del self._relations[relation_id]

    def exists(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType,
    ) -> bool:
        return any(
            relation.organization_id == organization_id
            and relation.source_object_id == source_object_id
            and relation.target_object_id == target_object_id
            and relation.relation_type == relation_type
            for relation in self._relations.values()
        )

    def outgoing(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> Sequence[KnowledgeObjectRelation]:
        return self._filter_relations(
            organization_id=organization_id,
            source_object_id=source_object_id,
            relation_type=relation_type,
        )

    def incoming(
        self,
        organization_id: OrganizationId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> Sequence[KnowledgeObjectRelation]:
        return self._filter_relations(
            organization_id=organization_id,
            target_object_id=target_object_id,
            relation_type=relation_type,
        )

    def snapshot(self) -> dict[UUID, KnowledgeObjectRelation]:
        return dict(self._relations)

    def restore(self, snapshot: dict[UUID, KnowledgeObjectRelation]) -> None:
        self._relations = dict(snapshot)

    def _filter_relations(
        self,
        *,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId | None = None,
        target_object_id: KnowledgeObjectId | None = None,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> tuple[KnowledgeObjectRelation, ...]:
        relations = [
            relation
            for relation in self._relations.values()
            if relation.organization_id == organization_id
            and (
                source_object_id is None
                or relation.source_object_id == source_object_id
            )
            and (
                target_object_id is None
                or relation.target_object_id == target_object_id
            )
            and (relation_type is None or relation.relation_type == relation_type)
        ]

        return tuple(
            sorted(
                relations,
                key=lambda relation: (
                    relation.created_at,
                    str(relation.relation_id),
                ),
            )
        )
