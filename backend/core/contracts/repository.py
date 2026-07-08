from __future__ import annotations

from typing import Generic, Iterable, Protocol, TypeVar

from backend.core.contracts.entity import EntityContract, EntityId


EntityT = TypeVar("EntityT", bound=EntityContract)


class RepositoryContract(Protocol, Generic[EntityT]):
    """Storage-agnostic repository contract."""

    def get(self, entity_id: EntityId) -> EntityT | None:
        ...

    def list(self) -> Iterable[EntityT]:
        ...

    def save(self, entity: EntityT) -> EntityT:
        ...

    def delete(self, entity_id: EntityId) -> None:
        ...
