from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.core.knowledge.models import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)


def test_knowledge_object_creation() -> None:
    now = datetime.now(UTC)
    header = KnowledgeObjectHeader(
        id=uuid4(),
        object_type="Organization",
        organization_id=uuid4(),
        status=KnowledgeObjectStatus.DRAFT,
        version=1,
        created_at=now,
        updated_at=now,
    )

    knowledge_object = KnowledgeObject(
        header=header,
        payload={"name": "SafetyMAIN"},
    )

    assert knowledge_object.header == header
    assert knowledge_object.payload == {"name": "SafetyMAIN"}


def test_payload_defaults_to_empty_dictionary() -> None:
    now = datetime.now(UTC)
    header = KnowledgeObjectHeader(
        id=uuid4(),
        object_type="Equipment",
        organization_id=uuid4(),
        status=KnowledgeObjectStatus.ACTIVE,
        version=1,
        created_at=now,
        updated_at=now,
    )

    knowledge_object = KnowledgeObject(header=header)

    assert knowledge_object.payload == {}


def test_enum_validation_rejects_unknown_status() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Employee",
            organization_id=uuid4(),
            status="UNKNOWN",
            version=1,
            created_at=now,
            updated_at=now,
        )


def test_invalid_version_is_rejected() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Regulation",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.DRAFT,
            version=0,
            created_at=now,
            updated_at=now,
        )


def test_uuid_validation_rejects_invalid_uuid() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        KnowledgeObjectHeader(
            id="not-a-uuid",
            object_type="Obligation",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.DRAFT,
            version=1,
            created_at=now,
            updated_at=now,
        )


def test_header_frozen_fields_cannot_be_changed() -> None:
    now = datetime.now(UTC)
    header = KnowledgeObjectHeader(
        id=uuid4(),
        object_type="Organization",
        organization_id=uuid4(),
        status=KnowledgeObjectStatus.DRAFT,
        version=1,
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(ValidationError):
        header.id = UUID("00000000-0000-0000-0000-000000000000")


def test_header_mutable_fields_can_be_changed() -> None:
    now = datetime.now(UTC)
    later = datetime.now(UTC)
    header = KnowledgeObjectHeader(
        id=uuid4(),
        object_type="Organization",
        organization_id=uuid4(),
        status=KnowledgeObjectStatus.DRAFT,
        version=1,
        created_at=now,
        updated_at=now,
    )

    header.status = KnowledgeObjectStatus.ACTIVE
    header.version = 2
    header.updated_at = later

    assert header.status is KnowledgeObjectStatus.ACTIVE
    assert header.version.value == 2
    assert header.updated_at == later
