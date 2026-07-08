from __future__ import annotations

from typing import Any, Iterable, Mapping, Protocol


MetadataSchemaId = str
MetadataFieldName = str
MetadataFieldType = str


class MetadataFieldContract(Protocol):
    """Contract for metadata field definitions."""

    name: MetadataFieldName
    type: MetadataFieldType
    required: bool
    default: Any
    attributes: Mapping[str, Any]


class MetadataSchemaContract(Protocol):
    """Contract for metadata schemas."""

    id: MetadataSchemaId
    name: str
    version: int
    fields: Iterable[MetadataFieldContract]


class MetadataProviderContract(Protocol):
    """Contract for retrieving metadata schemas."""

    def get_schema(self, schema_id: MetadataSchemaId) -> MetadataSchemaContract | None:
        ...
