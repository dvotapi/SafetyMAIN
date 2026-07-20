from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects import KnowledgeObjectType
from backend.core.domain.value_objects.knowledge_object_search_criteria import JSONValue

HTTP_KNOWLEDGE_OBJECT_STATUSES: dict[str, KnowledgeObjectStatus] = {
    "active": KnowledgeObjectStatus.ACTIVE,
    "archived": KnowledgeObjectStatus.ARCHIVED,
    "deleted": KnowledgeObjectStatus.DELETED,
}


@dataclass(frozen=True, slots=True)
class KnowledgeObjectSearchParams:
    object_type: KnowledgeObjectType | None
    status: KnowledgeObjectStatus | None
    metadata_equals: Mapping[str, JSONValue]
    include_deleted: bool
    offset: int
    limit: int


def _validation_error(message: str, *, loc: tuple[str, ...]) -> RequestValidationError:
    return RequestValidationError(
        [
            {
                "loc": loc,
                "msg": message,
                "type": "value_error",
            }
        ]
    )


def _parse_metadata_json(raw_value: str) -> Mapping[str, JSONValue]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: set[str] = set()
        parsed: dict[str, Any] = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError("Duplicate metadata keys are not allowed.")
            seen.add(key)
            parsed[key] = value
        return parsed

    try:
        decoded = json.loads(raw_value, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ValueError("Metadata must be valid JSON.") from exc
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if not isinstance(decoded, dict):
        raise ValueError("Metadata must be a JSON object.")

    _reject_non_finite_values(decoded)
    return decoded


def _reject_non_finite_values(value: Any) -> None:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("Metadata must not contain NaN or Infinity.")
        return

    if isinstance(value, dict):
        for item in value.values():
            _reject_non_finite_values(item)
        return

    if isinstance(value, list):
        for item in value:
            _reject_non_finite_values(item)


def _parse_status(raw_value: str) -> KnowledgeObjectStatus:
    normalized = raw_value.strip().lower()
    if not normalized:
        raise ValueError("Status must not be empty.")

    try:
        return HTTP_KNOWLEDGE_OBJECT_STATUSES[normalized]
    except KeyError as exc:
        raise ValueError(
            "Status must be one of: active, archived, deleted."
        ) from exc


def _parse_object_type(raw_value: str) -> KnowledgeObjectType:
    stripped = raw_value.strip()
    if not stripped:
        raise ValueError("Type must not be empty.")
    return KnowledgeObjectType(value=stripped)


def parse_knowledge_object_search_params(
    type: Annotated[
        str | None,
        Query(
            description="Exact Knowledge Object type filter (case-insensitive).",
        ),
    ] = None,
    status: Annotated[
        str | None,
        Query(
            description=(
                "Lifecycle status filter. Allowed values: active, archived, deleted."
            ),
        ),
    ] = None,
    metadata: Annotated[
        str | None,
        Query(
            description=(
                "URL-encoded JSON object with metadata equality filters. "
                "All keys are combined with AND semantics. Example: "
                '{"department":"security","approved":true}'
            ),
        ),
    ] = None,
    include_deleted: Annotated[
        bool | None,
        Query(
            description=(
                "When true, deleted objects may appear in results unless "
                "status excludes them. Defaults to false."
            ),
        ),
    ] = None,
    offset: Annotated[
        int,
        Query(ge=0, description="Pagination offset. Defaults to 0."),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of results per page. Defaults to 50.",
        ),
    ] = 50,
) -> KnowledgeObjectSearchParams:
    parsed_status: KnowledgeObjectStatus | None = None
    parsed_type: KnowledgeObjectType | None = None
    metadata_equals: Mapping[str, JSONValue] = {}

    if type is not None:
        try:
            parsed_type = _parse_object_type(type)
        except (ValidationError, ValueError) as exc:
            raise _validation_error(str(exc), loc=("query", "type")) from exc

    if status is not None:
        try:
            parsed_status = _parse_status(status)
        except ValueError as exc:
            raise _validation_error(str(exc), loc=("query", "status")) from exc

    if metadata is not None:
        try:
            metadata_equals = _parse_metadata_json(metadata)
        except ValueError as exc:
            raise _validation_error(str(exc), loc=("query", "metadata")) from exc

    if parsed_status is KnowledgeObjectStatus.DELETED and include_deleted is False:
        raise _validation_error(
            "status=deleted cannot be combined with include_deleted=false.",
            loc=("query", "include_deleted"),
        )

    return KnowledgeObjectSearchParams(
        object_type=parsed_type,
        status=parsed_status,
        metadata_equals=metadata_equals,
        include_deleted=include_deleted if include_deleted is not None else False,
        offset=offset,
        limit=limit,
    )
