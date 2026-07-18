from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObjectRelation,
    KnowledgeObjectRelationNotFound,
    SelfReferencingKnowledgeObjectRelation,
)
from backend.core.domain.repositories import KnowledgeObjectRelationRepositoryContract
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers import (
    relation_to_domain,
    relation_to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models import (
    KnowledgeObjectRelationModel,
)


class SQLAlchemyKnowledgeObjectRelationRepository(
    KnowledgeObjectRelationRepositoryContract
):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, relation: KnowledgeObjectRelation) -> None:
        if relation.source_object_id == relation.target_object_id:
            raise SelfReferencingKnowledgeObjectRelation(relation.source_object_id)

        if self._get_model(relation.relation_id) is not None or self.exists(
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

        self._session.add(relation_to_model(relation))

    def get(self, relation_id: UUID) -> KnowledgeObjectRelation:
        model = self._get_model(relation_id)

        if model is None:
            raise KnowledgeObjectRelationNotFound(relation_id)

        return relation_to_domain(model)

    def remove(self, relation_id: UUID) -> None:
        statement = delete(KnowledgeObjectRelationModel).where(
            KnowledgeObjectRelationModel.relation_id == relation_id
        )
        result = self._session.execute(statement)

        if result.rowcount != 1:
            raise KnowledgeObjectRelationNotFound(relation_id)

    def exists(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType,
    ) -> bool:
        statement = select(
            exists().where(
                KnowledgeObjectRelationModel.organization_id == organization_id.value,
                KnowledgeObjectRelationModel.source_object_id == source_object_id.value,
                KnowledgeObjectRelationModel.target_object_id == target_object_id.value,
                KnowledgeObjectRelationModel.relation_type == relation_type.value,
            )
        )

        return bool(self._session.scalar(statement))

    def outgoing(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> Sequence[KnowledgeObjectRelation]:
        filters = [
            KnowledgeObjectRelationModel.organization_id == organization_id.value,
            KnowledgeObjectRelationModel.source_object_id == source_object_id.value,
        ]
        if relation_type is not None:
            filters.append(KnowledgeObjectRelationModel.relation_type == relation_type.value)

        return self._find_relations(filters)

    def incoming(
        self,
        organization_id: OrganizationId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> Sequence[KnowledgeObjectRelation]:
        filters = [
            KnowledgeObjectRelationModel.organization_id == organization_id.value,
            KnowledgeObjectRelationModel.target_object_id == target_object_id.value,
        ]
        if relation_type is not None:
            filters.append(KnowledgeObjectRelationModel.relation_type == relation_type.value)

        return self._find_relations(filters)

    def _get_model(self, relation_id: UUID) -> KnowledgeObjectRelationModel | None:
        return self._session.get(KnowledgeObjectRelationModel, relation_id)

    def _find_relations(self, filters: Sequence[Any]) -> tuple[KnowledgeObjectRelation, ...]:
        statement = (
            select(KnowledgeObjectRelationModel)
            .where(*filters)
            .order_by(
                KnowledgeObjectRelationModel.created_at.asc(),
                KnowledgeObjectRelationModel.relation_id.asc(),
            )
        )

        return tuple(
            relation_to_domain(model)
            for model in self._session.scalars(statement).all()
        )
