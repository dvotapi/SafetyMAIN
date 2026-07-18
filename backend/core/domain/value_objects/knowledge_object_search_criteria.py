from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects.knowledge_object_type import KnowledgeObjectType
from backend.core.domain.value_objects.organization_id import OrganizationId


JSONValue: TypeAlias = object

MAX_SEARCH_LIMIT = 100


class KnowledgeObjectSearchCriteria(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    organization_id: OrganizationId
    object_type: KnowledgeObjectType | None = None
    status: KnowledgeObjectStatus | None = None
    metadata_equals: Mapping[str, JSONValue] = Field(default_factory=dict)
    limit: int = Field(ge=1, le=MAX_SEARCH_LIMIT)
    offset: int = Field(ge=0)

    @field_validator("metadata_equals")
    @classmethod
    def validate_metadata_equals(
        cls,
        metadata_equals: Mapping[str, JSONValue],
    ) -> Mapping[str, JSONValue]:
        normalized_metadata: dict[str, JSONValue] = {}

        for key, value in metadata_equals.items():
            if not key.strip():
                raise ValueError("Metadata filter keys must not be empty.")

            normalized_metadata[key] = _validate_json_value(value)

        return MappingProxyType(normalized_metadata)


def _validate_json_value(value: Any) -> JSONValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if isinstance(value, list | tuple):
        return tuple(_validate_json_value(item) for item in value)

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _validate_json_value(item)
                for key, item in value.items()
                if _is_json_object_key(key)
            }
        )

    raise ValueError(f"Metadata filter value is not JSON-compatible: {value!r}")


def _is_json_object_key(key: Any) -> bool:
    if isinstance(key, str):
        return True

    raise ValueError(f"JSON object keys must be strings: {key!r}")
