from __future__ import annotations

from typing import Iterable

from backend.core.domain.entities.knowledge_object import KnowledgeObject
from backend.core.domain.repositories import KnowledgeObjectRepositoryContract
from backend.core.domain.value_objects import KnowledgeObjectId


class InMemoryKnowledgeObjectRepository(KnowledgeObjectRepositoryContract):
    def __init__(self) -> None:
        self._objects: dict[KnowledgeObjectId, KnowledgeObject] = {}
        self._history: dict[KnowledgeObjectId, list[KnowledgeObject]] = {}

    def get(self, object_id: KnowledgeObjectId) -> KnowledgeObject | None:
        return self._objects.get(object_id)

    def list(self) -> Iterable[KnowledgeObject]:
        return tuple(self._objects.values())

    def save(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        self._objects[knowledge_object.header.id] = knowledge_object
        return knowledge_object

    def update(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        object_id = knowledge_object.header.id
        current_object = self._objects.get(object_id)

        if current_object is not None:
            self._history.setdefault(object_id, []).append(current_object)

        self._objects[object_id] = knowledge_object
        return knowledge_object

    def archive(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        return self.update(knowledge_object)

    def restore(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        return self.update(knowledge_object)

    def history(self, object_id: KnowledgeObjectId) -> Iterable[KnowledgeObject]:
        return tuple(self._history.get(object_id, ()))

    def delete(self, object_id: KnowledgeObjectId) -> None:
        self._objects.pop(object_id, None)
