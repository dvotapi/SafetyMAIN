from __future__ import annotations

import json

import pytest
from fastapi.exceptions import RequestValidationError

from backend.api.params.knowledge_object_search import (
    _parse_metadata_json,
    parse_knowledge_object_search_params,
)
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects import KnowledgeObjectType


def test_parse_metadata_json_accepts_object_with_typed_values() -> None:
    parsed = _parse_metadata_json(
        '{"department":"security","approved":true,"revision":3,"nested":{"values":[1,false,null]}}'
    )

    assert parsed == {
        "department": "security",
        "approved": True,
        "revision": 3,
        "nested": {"values": [1, False, None]},
    }


def test_parse_metadata_json_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="Duplicate metadata keys"):
        _parse_metadata_json('{"department":"security","department":"legal"}')


def test_parse_metadata_json_rejects_top_level_array() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        _parse_metadata_json("[1, 2]")


def test_parse_metadata_json_rejects_top_level_scalar() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        _parse_metadata_json('"value"')


def test_parse_metadata_json_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="valid JSON"):
        _parse_metadata_json("{not-json")


def test_parse_metadata_json_rejects_non_finite_floats() -> None:
    encoded = json.dumps({"value": float("inf")})
    with pytest.raises(ValueError, match="NaN or Infinity"):
        _parse_metadata_json(encoded)


def test_parse_metadata_json_accepts_empty_object() -> None:
    assert _parse_metadata_json("{}") == {}


def test_parse_search_params_defaults() -> None:
    params = parse_knowledge_object_search_params()

    assert params.object_type is None
    assert params.status is None
    assert params.metadata_equals == {}
    assert params.include_deleted is False
    assert params.offset == 0
    assert params.limit == 50


def test_parse_search_params_maps_type_and_status() -> None:
    params = parse_knowledge_object_search_params(
        type=" Policy ",
        status="ACTIVE",
    )

    assert params.object_type == KnowledgeObjectType(value="policy")
    assert params.status is KnowledgeObjectStatus.ACTIVE


def test_parse_search_params_rejects_empty_type() -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        parse_knowledge_object_search_params(type="   ")

    assert exc_info.value.errors()[0]["loc"] == ("query", "type")


def test_parse_search_params_rejects_invalid_status() -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        parse_knowledge_object_search_params(status="pending")

    assert exc_info.value.errors()[0]["loc"] == ("query", "status")


def test_parse_search_params_rejects_deleted_with_include_deleted_false() -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        parse_knowledge_object_search_params(status="deleted", include_deleted=False)

    assert exc_info.value.errors()[0]["loc"] == ("query", "include_deleted")
