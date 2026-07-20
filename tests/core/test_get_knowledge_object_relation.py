from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationCommand,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.application.handlers.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationHandler,
)
from backend.core.application.handlers.get_knowledge_object_relation import (
    GetKnowledgeObjectRelationHandler,
)
from backend.core.application.queries.get_knowledge_object_relation import (
    GetKnowledgeObjectRelationQuery,
)
from backend.core.domain.exceptions import KnowledgeObjectRelationNotFound
from backend.core.domain.value_objects import KnowledgeObjectRelationType, OrganizationId
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_get_relation_query_returns_relation_for_matching_organization() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = uuid4()
    source = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(object_type="Instruction", organization_id=organization_id)
    )
    target = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(object_type="Risk", organization_id=organization_id)
    )
    relation = CreateKnowledgeObjectRelationHandler(unit_of_work).handle(
        CreateKnowledgeObjectRelationCommand(
            organization_id=source.header.organization_id,
            source_object_id=source.header.id,
            target_object_id=target.header.id,
            relation_type=KnowledgeObjectRelationType(value="uses"),
        )
    )

    result = GetKnowledgeObjectRelationHandler(unit_of_work).handle(
        GetKnowledgeObjectRelationQuery(
            organization_id=source.header.organization_id,
            relation_id=relation.relation_id,
        )
    )

    assert result == relation


def test_get_relation_query_hides_cross_organization_access() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = uuid4()
    source = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(object_type="Instruction", organization_id=organization_id)
    )
    target = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(object_type="Risk", organization_id=organization_id)
    )
    relation = CreateKnowledgeObjectRelationHandler(unit_of_work).handle(
        CreateKnowledgeObjectRelationCommand(
            organization_id=source.header.organization_id,
            source_object_id=source.header.id,
            target_object_id=target.header.id,
            relation_type=KnowledgeObjectRelationType(value="uses"),
        )
    )

    with pytest.raises(KnowledgeObjectRelationNotFound):
        GetKnowledgeObjectRelationHandler(unit_of_work).handle(
            GetKnowledgeObjectRelationQuery(
                organization_id=OrganizationId(value=uuid4()),
                relation_id=relation.relation_id,
            )
        )
