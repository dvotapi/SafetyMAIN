from __future__ import annotations

from typing import BinaryIO, Protocol


StorageKey = str
ContentType = str


class StorageObjectContract(Protocol):
    """Contract for stored binary objects."""

    key: StorageKey
    content_type: ContentType
    size: int


class StorageContract(Protocol):
    """Storage-agnostic binary object storage contract."""

    def exists(self, key: StorageKey) -> bool:
        ...

    def open(self, key: StorageKey) -> BinaryIO:
        ...

    def put(
        self,
        key: StorageKey,
        content: BinaryIO,
        content_type: ContentType,
    ) -> StorageObjectContract:
        ...

    def delete(self, key: StorageKey) -> None:
        ...
