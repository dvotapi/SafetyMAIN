from __future__ import annotations

from types import TracebackType

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.repositories import (
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
)
from backend.core.infrastructure.persistence.in_memory.knowledge_object_repository import (
    InMemoryKnowledgeObjectRepository,
)
from backend.core.infrastructure.persistence.in_memory.knowledge_object_relation_repository import (
    InMemoryKnowledgeObjectRelationRepository,
)


class InMemoryUnitOfWork(UnitOfWorkContract):
    def __init__(
        self,
        knowledge_objects: KnowledgeObjectRepositoryContract | None = None,
        relations: KnowledgeObjectRelationRepositoryContract | None = None,
    ) -> None:
        self._knowledge_objects = knowledge_objects or InMemoryKnowledgeObjectRepository()
        self._relations = relations or InMemoryKnowledgeObjectRelationRepository()
        self._knowledge_objects_snapshot: object | None = None
        self._relations_snapshot: object | None = None
        self.committed = False
        self.rolled_back = False

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        return self._knowledge_objects

    @property
    def relations(self) -> KnowledgeObjectRelationRepositoryContract:
        return self._relations

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self._restore_snapshots()
        self.rolled_back = True

    def __enter__(self) -> InMemoryUnitOfWork:
        self._create_snapshots()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None or not self.committed:
            self.rollback()

    def _create_snapshots(self) -> None:
        if hasattr(self._knowledge_objects, "snapshot"):
            self._knowledge_objects_snapshot = self._knowledge_objects.snapshot()
        if hasattr(self._relations, "snapshot"):
            self._relations_snapshot = self._relations.snapshot()

    def _restore_snapshots(self) -> None:
        if (
            self._knowledge_objects_snapshot is not None
            and hasattr(self._knowledge_objects, "restore")
        ):
            self._knowledge_objects.restore(self._knowledge_objects_snapshot)
        if self._relations_snapshot is not None and hasattr(self._relations, "restore"):
            self._relations.restore(self._relations_snapshot)
