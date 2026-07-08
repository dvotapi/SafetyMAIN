from __future__ import annotations

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.repositories import KnowledgeObjectRepositoryContract
from backend.core.infrastructure.persistence.in_memory.knowledge_object_repository import (
    InMemoryKnowledgeObjectRepository,
)


class InMemoryUnitOfWork(UnitOfWorkContract):
    def __init__(
        self,
        knowledge_objects: KnowledgeObjectRepositoryContract | None = None,
    ) -> None:
        self._knowledge_objects = knowledge_objects or InMemoryKnowledgeObjectRepository()
        self.committed = False
        self.rolled_back = False

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        return self._knowledge_objects

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True
