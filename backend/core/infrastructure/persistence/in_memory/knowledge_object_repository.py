from __future__ import annotations

from collections.abc import Mapping
from typing import Sequence

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
    JSONValue,
    KnowledgeObjectSearchCriteria,
)
from backend.core.domain.value_objects.knowledge_object_search_result import (
    KnowledgeObjectSearchResult,
)


class InMemoryKnowledgeObjectRepository(KnowledgeObjectRepositoryContract):
    def __init__(self) -> None:
        self._objects: dict[KnowledgeObjectId, KnowledgeObject] = {}
        self._history: dict[KnowledgeObjectId, list[KnowledgeObject]] = {}

    def add(self, knowledge_object: KnowledgeObject) -> None:
        if knowledge_object.header.id in self._objects:
            raise DuplicateKnowledgeObject(knowledge_object.header.id)

        self._objects[knowledge_object.header.id] = knowledge_object

    def get(self, object_id: KnowledgeObjectId) -> KnowledgeObject:
        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise KnowledgeObjectNotFound(object_id) from exc

    def update(self, knowledge_object: KnowledgeObject) -> None:
        object_id = knowledge_object.header.id
        current_object = self._objects.get(object_id)

        if current_object is None:
            raise KnowledgeObjectNotFound(object_id)

        expected_version = current_object.header.version.value + 1
        if knowledge_object.header.version.value != expected_version:
            raise KnowledgeObjectVersionConflict(
                knowledge_object_id=object_id,
                expected_version=KnowledgeObjectVersion(value=expected_version),
                actual_version=knowledge_object.header.version,
            )

        self._history.setdefault(object_id, []).append(current_object)
        self._objects[object_id] = knowledge_object

    def history(self, object_id: KnowledgeObjectId) -> Sequence[KnowledgeObject]:
        if object_id not in self._objects:
            raise KnowledgeObjectNotFound(object_id)

        return tuple(self._history.get(object_id, ()))

    def search(
        self,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> KnowledgeObjectSearchResult:
        matching_objects = [
            knowledge_object
            for knowledge_object in self._objects.values()
            if self._matches_search_criteria(knowledge_object, criteria)
        ]
        ordered_objects = tuple(
            sorted(
                matching_objects,
                key=lambda knowledge_object: (
                    knowledge_object.header.created_at,
                    str(knowledge_object.header.id.value),
                ),
            )
        )
        paged_objects = ordered_objects[
            criteria.offset : criteria.offset + criteria.limit
        ]

        return KnowledgeObjectSearchResult.create(
            items=paged_objects,
            total=len(ordered_objects),
            limit=criteria.limit,
            offset=criteria.offset,
        )

    def snapshot(
        self,
    ) -> tuple[dict[KnowledgeObjectId, KnowledgeObject], dict[KnowledgeObjectId, list[KnowledgeObject]]]:
        return (
            dict(self._objects),
            {object_id: list(history) for object_id, history in self._history.items()},
        )

    def restore(
        self,
        snapshot: tuple[
            dict[KnowledgeObjectId, KnowledgeObject],
            dict[KnowledgeObjectId, list[KnowledgeObject]],
        ],
    ) -> None:
        objects, history = snapshot
        self._objects = dict(objects)
        self._history = {
            object_id: list(object_history)
            for object_id, object_history in history.items()
        }

    def _matches_search_criteria(
        self,
        knowledge_object: KnowledgeObject,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> bool:
        return (
            knowledge_object.header.organization_id == criteria.organization_id
            and self._matches_status(knowledge_object, criteria)
            and self._matches_object_type(knowledge_object, criteria)
            and self._matches_metadata(knowledge_object, criteria)
        )

    def _matches_status(
        self,
        knowledge_object: KnowledgeObject,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> bool:
        if criteria.status is not None:
            return knowledge_object.header.status is criteria.status

        return knowledge_object.header.status in (
            KnowledgeObjectStatus.ACTIVE,
            KnowledgeObjectStatus.ARCHIVED,
        )

    def _matches_object_type(
        self,
        knowledge_object: KnowledgeObject,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> bool:
        if criteria.object_type is None:
            return True

        return knowledge_object.header.object_type == criteria.object_type

    def _matches_metadata(
        self,
        knowledge_object: KnowledgeObject,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> bool:
        return all(
            key in knowledge_object.payload
            and _json_values_equal(knowledge_object.payload[key], expected_value)
            for key, expected_value in criteria.metadata_equals.items()
        )


def _json_values_equal(actual_value: object, expected_value: JSONValue) -> bool:
    if isinstance(actual_value, Mapping) and isinstance(expected_value, Mapping):
        return actual_value.keys() == expected_value.keys() and all(
            _json_values_equal(actual_value[key], expected_value[key])
            for key in actual_value
        )

    if isinstance(actual_value, list | tuple) and isinstance(expected_value, list | tuple):
        return len(actual_value) == len(expected_value) and all(
            _json_values_equal(actual_item, expected_item)
            for actual_item, expected_item in zip(actual_value, expected_value, strict=True)
        )

    if type(actual_value) is not type(expected_value):
        return False

    return actual_value == expected_value
