from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers import (
    to_domain,
    to_domain_from_history,
    to_history_model,
    to_model,
)


def test_knowledge_object_mapping_round_trip_preserves_domain_values() -> None:
    now = datetime.now(UTC)
    domain_object = KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Instruction",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.ACTIVE,
            version=2,
            created_at=now,
            updated_at=now,
        ),
        payload={"department": "production", "approved": True},
    )

    model = to_model(domain_object)
    mapped_domain_object = to_domain(model)

    assert mapped_domain_object == domain_object


def test_history_mapping_round_trip_preserves_domain_values() -> None:
    now = datetime.now(UTC)
    domain_object = KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Risk",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.ARCHIVED,
            version=1,
            created_at=now,
            updated_at=now,
        ),
        payload={"risk_level": 3},
    )

    history_model = to_history_model(domain_object, recorded_at=now)
    mapped_domain_object = to_domain_from_history(history_model)

    assert mapped_domain_object == domain_object
