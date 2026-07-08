from __future__ import annotations

from typing import Protocol

from backend.core.domain.repositories import KnowledgeObjectRepositoryContract


class UnitOfWorkContract(Protocol):
    """Coordinates repository operations for an application use case."""

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...
