from __future__ import annotations

from typing import Annotated

from fastapi import Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.core.application.queries.relation_direction import RelationDirection
from backend.core.domain.value_objects import KnowledgeObjectRelationType

HTTP_RELATION_DIRECTIONS: dict[str, RelationDirection] = {
    "outgoing": RelationDirection.OUTGOING,
    "incoming": RelationDirection.INCOMING,
    "both": RelationDirection.BOTH,
}


def parse_relation_direction(value: str | None) -> RelationDirection:
    if value is None:
        return RelationDirection.OUTGOING

    normalized = value.strip().lower()
    try:
        return HTTP_RELATION_DIRECTIONS[normalized]
    except KeyError as exc:
        raise ValueError(
            "Direction must be one of: outgoing, incoming, both."
        ) from exc


def parse_optional_relation_type(
    value: str | None,
) -> KnowledgeObjectRelationType | None:
    if value is None:
        return None
    return KnowledgeObjectRelationType(value=value)


def optional_relation_type_query(
    type: Annotated[str | None, Query(alias="type")] = None,
) -> KnowledgeObjectRelationType | None:
    try:
        return parse_optional_relation_type(type)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def connected_direction_query(
    direction: Annotated[str | None, Query(alias="direction")] = None,
) -> RelationDirection:
    try:
        return parse_relation_direction(direction)
    except ValueError as exc:
        raise RequestValidationError(
            [
                {
                    "loc": ("query", "direction"),
                    "msg": str(exc),
                    "type": "value_error",
                }
            ]
        ) from exc
