from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectType,
    KnowledgeObjectVersion,
    OrganizationId,
)


def test_knowledge_object_id_wraps_uuid() -> None:
    value = uuid4()

    knowledge_object_id = KnowledgeObjectId(value=value)

    assert knowledge_object_id.value == value


def test_knowledge_object_id_rejects_invalid_uuid() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObjectId(value="not-a-uuid")


def test_organization_id_wraps_uuid() -> None:
    value = uuid4()

    organization_id = OrganizationId(value=value)

    assert organization_id.value == value


def test_organization_id_rejects_invalid_uuid() -> None:
    with pytest.raises(ValidationError):
        OrganizationId(value="not-a-uuid")


def test_knowledge_object_type_is_normalized_to_lowercase() -> None:
    knowledge_object_type = KnowledgeObjectType(value=" Organization ")

    assert knowledge_object_type.value == "organization"


def test_knowledge_object_type_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObjectType(value="   ")


def test_knowledge_object_version_accepts_positive_integer() -> None:
    version = KnowledgeObjectVersion(value=1)

    assert version.value == 1


def test_knowledge_object_version_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObjectVersion(value=0)


def test_value_objects_are_immutable() -> None:
    version = KnowledgeObjectVersion(value=1)

    with pytest.raises(ValidationError):
        version.value = 2
