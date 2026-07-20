from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.update_knowledge_object import (
    UpdateKnowledgeObjectCommand,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.application.handlers.get_knowledge_object import GetKnowledgeObjectHandler
from backend.core.application.handlers.get_knowledge_object_history import (
    GetKnowledgeObjectHistoryHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.application.queries.get_knowledge_object import GetKnowledgeObjectQuery
from backend.core.application.queries.get_knowledge_object_history import (
    GetKnowledgeObjectHistoryQuery,
)
from backend.core.domain.exceptions import KnowledgeObjectNotFound, KnowledgeObjectVersionConflict
from backend.core.domain.value_objects import KnowledgeObjectVersion, OrganizationId
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_get_knowledge_object_query_returns_object_for_matching_organization() -> None:
    unit_of_work = InMemoryUnitOfWork()
    created = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(
            object_type="policy",
            organization_id=uuid4(),
            payload={"title": "Policy"},
        )
    )

    result = GetKnowledgeObjectHandler(unit_of_work).handle(
        GetKnowledgeObjectQuery(
            organization_id=created.header.organization_id,
            object_id=created.header.id,
        )
    )

    assert result == created


def test_get_knowledge_object_query_hides_cross_organization_access() -> None:
    unit_of_work = InMemoryUnitOfWork()
    created = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(
            object_type="policy",
            organization_id=uuid4(),
            payload={"title": "Policy"},
        )
    )

    with pytest.raises(KnowledgeObjectNotFound):
        GetKnowledgeObjectHandler(unit_of_work).handle(
            GetKnowledgeObjectQuery(
                organization_id=OrganizationId(value=uuid4()),
                object_id=created.header.id,
            )
        )


def test_get_history_returns_previous_versions_only() -> None:
    unit_of_work = InMemoryUnitOfWork()
    created = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(
            object_type="policy",
            organization_id=uuid4(),
            payload={"title": "Version 1"},
        )
    )
    UpdateKnowledgeObjectHandler(unit_of_work).handle(
        UpdateKnowledgeObjectCommand(
            object_id=created.header.id,
            organization_id=created.header.organization_id,
            expected_version=KnowledgeObjectVersion(value=1),
            payload={"title": "Version 2"},
        )
    )

    history = GetKnowledgeObjectHistoryHandler(unit_of_work).handle(
        GetKnowledgeObjectHistoryQuery(
            organization_id=created.header.organization_id,
            object_id=created.header.id,
        )
    )

    assert len(history) == 1
    assert history[0].header.version.value == 1


def test_update_with_stale_expected_version_raises_conflict() -> None:
    unit_of_work = InMemoryUnitOfWork()
    created = CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(
            object_type="policy",
            organization_id=uuid4(),
        )
    )

    with pytest.raises(KnowledgeObjectVersionConflict):
        UpdateKnowledgeObjectHandler(unit_of_work).handle(
            UpdateKnowledgeObjectCommand(
                object_id=created.header.id,
                organization_id=created.header.organization_id,
                expected_version=KnowledgeObjectVersion(value=2),
                payload={"title": "Stale"},
            )
        )
