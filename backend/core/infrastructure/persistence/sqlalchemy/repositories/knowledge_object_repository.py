from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObject,
    KnowledgeObjectNotFound,
    KnowledgeObjectVersionConflict,
)
from backend.core.domain.repositories import KnowledgeObjectRepositoryContract
from backend.core.domain.value_objects import KnowledgeObjectId, KnowledgeObjectVersion
from backend.core.domain.value_objects.knowledge_object_search_criteria import (
    KnowledgeObjectSearchCriteria,
)
from backend.core.domain.value_objects.knowledge_object_search_result import (
    KnowledgeObjectSearchResult,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers import (
    apply_to_model,
    to_domain,
    to_domain_from_history,
    to_history_model,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models import (
    KnowledgeObjectModel,
    KnowledgeObjectVersionModel,
)


class SQLAlchemyKnowledgeObjectRepository(KnowledgeObjectRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, knowledge_object: KnowledgeObject) -> None:
        if self._get_model(knowledge_object.header.id) is not None:
            raise DuplicateKnowledgeObject(knowledge_object.header.id)

        self._session.add(to_model(knowledge_object))

    def get(self, object_id: KnowledgeObjectId) -> KnowledgeObject:
        model = self._get_model(object_id)

        if model is None:
            raise KnowledgeObjectNotFound(object_id)

        return to_domain(model)

    def update(self, knowledge_object: KnowledgeObject) -> None:
        model = self._get_model(knowledge_object.header.id, with_for_update=True)

        if model is None:
            raise KnowledgeObjectNotFound(knowledge_object.header.id)

        expected_version = model.version + 1
        incoming_version = knowledge_object.header.version.value
        if incoming_version != expected_version:
            raise KnowledgeObjectVersionConflict(
                knowledge_object_id=knowledge_object.header.id,
                expected_version=KnowledgeObjectVersion(value=expected_version),
                actual_version=knowledge_object.header.version,
            )

        self._session.add(to_history_model(to_domain(model)))
        apply_to_model(model, knowledge_object)

    def history(self, object_id: KnowledgeObjectId) -> Sequence[KnowledgeObject]:
        if self._get_model(object_id) is None:
            raise KnowledgeObjectNotFound(object_id)

        statement = (
            select(KnowledgeObjectVersionModel)
            .where(KnowledgeObjectVersionModel.knowledge_object_id == object_id.value)
            .order_by(KnowledgeObjectVersionModel.version.asc())
        )

        return tuple(
            to_domain_from_history(model)
            for model in self._session.scalars(statement).all()
        )

    def search(
        self,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> KnowledgeObjectSearchResult:
        filters = self._build_search_filters(criteria)
        base_statement = select(KnowledgeObjectModel).where(*filters)
        total_statement = select(func.count()).select_from(
            select(KnowledgeObjectModel.id).where(*filters).subquery()
        )
        total = self._session.scalar(total_statement) or 0
        items_statement = (
            base_statement.order_by(
                KnowledgeObjectModel.created_at.asc(),
                KnowledgeObjectModel.id.asc(),
            )
            .limit(criteria.limit)
            .offset(criteria.offset)
        )
        items = tuple(
            to_domain(model) for model in self._session.scalars(items_statement).all()
        )

        return KnowledgeObjectSearchResult.create(
            items=items,
            total=total,
            limit=criteria.limit,
            offset=criteria.offset,
        )

    def _get_model(
        self,
        object_id: KnowledgeObjectId,
        *,
        with_for_update: bool = False,
    ) -> KnowledgeObjectModel | None:
        return self._session.get(
            KnowledgeObjectModel,
            object_id.value,
            with_for_update=with_for_update,
        )

    def _build_search_filters(
        self,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> list[Any]:
        filters: list[Any] = [
            KnowledgeObjectModel.organization_id == criteria.organization_id.value
        ]

        if criteria.status is None:
            filters.append(
                KnowledgeObjectModel.status.in_(
                    (
                        KnowledgeObjectStatus.ACTIVE.value,
                        KnowledgeObjectStatus.ARCHIVED.value,
                    )
                )
            )
        else:
            filters.append(KnowledgeObjectModel.status == criteria.status.value)

        if criteria.object_type is not None:
            filters.append(KnowledgeObjectModel.object_type == criteria.object_type.value)

        filters.extend(self._build_metadata_filters(criteria))

        return filters

    def _build_metadata_filters(
        self,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> list[Any]:
        return [
            KnowledgeObjectModel.metadata_.contains({key: _to_plain_json(value)})
            for key, value in criteria.metadata_equals.items()
        ]


def _to_plain_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_plain_json(item) for key, item in value.items()}

    if isinstance(value, list | tuple):
        return [_to_plain_json(item) for item in value]

    return value
