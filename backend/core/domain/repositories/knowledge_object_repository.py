from __future__ import annotations

from typing import Iterable, Protocol

from backend.core.domain.entities.knowledge_object import KnowledgeObject
from backend.core.domain.value_objects import KnowledgeObjectId


class KnowledgeObjectRepositoryContract(Protocol):
    """Repository contract for Knowledge Objects."""

    def get(self, object_id: KnowledgeObjectId) -> KnowledgeObject | None:
        ...

    def list(self) -> Iterable[KnowledgeObject]:
        ...

    def save(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        ...

    def update(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        ...

    def archive(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        ...

    def restore(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        ...

    def history(self, object_id: KnowledgeObjectId) -> Iterable[KnowledgeObject]:
        ...

    def delete(self, object_id: KnowledgeObjectId) -> None:
        ...
