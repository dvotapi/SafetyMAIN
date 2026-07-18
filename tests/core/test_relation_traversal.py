from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationCommand,
)
from backend.core.application.commands.delete_knowledge_object import (
    DeleteKnowledgeObjectCommand,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.application.handlers.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationHandler,
)
from backend.core.application.handlers.delete_knowledge_object import (
    DeleteKnowledgeObjectHandler,
)
from backend.core.application.handlers.get_connected_knowledge_objects import (
    GetConnectedKnowledgeObjectsHandler,
)
from backend.core.application.handlers.get_incoming_relations import (
    GetIncomingRelationsHandler,
)
from backend.core.application.handlers.get_outgoing_relations import (
    GetOutgoingRelationsHandler,
)
from backend.core.application.queries.get_connected_knowledge_objects import (
    GetConnectedKnowledgeObjectsQuery,
)
from backend.core.application.queries.get_incoming_relations import (
    GetIncomingRelationsQuery,
)
from backend.core.application.queries.get_outgoing_relations import (
    GetOutgoingRelationsQuery,
)
from backend.core.application.queries.relation_direction import RelationDirection
from backend.core.domain.entities import KnowledgeObject, KnowledgeObjectRelation
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.exceptions import (
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectNotFound,
)
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
)
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_outgoing_relation_retrieval() -> None:
    unit_of_work, source, target = _create_relation_graph()
    relation = _create_relation(unit_of_work, source, target, "uses")

    result = GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
        )
    )

    assert result == (relation,)


def test_incoming_relation_retrieval() -> None:
    unit_of_work, source, target = _create_relation_graph()
    relation = _create_relation(unit_of_work, source, target, "uses")

    result = GetIncomingRelationsHandler(unit_of_work).handle(
        GetIncomingRelationsQuery(
            organization_id=target.header.organization_id,
            knowledge_object_id=target.header.id,
        )
    )

    assert result == (relation,)


def test_traversal_with_no_relations_returns_empty_sequence() -> None:
    unit_of_work, source, _target = _create_relation_graph(create_relation=False)

    result = GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
        )
    )

    assert result == ()


def test_traversal_filters_by_relation_type() -> None:
    unit_of_work, source, target = _create_relation_graph()
    uses_relation = _create_relation(unit_of_work, source, target, "uses")
    extra_target = _create_object(unit_of_work, source.header.organization_id.value)
    _create_relation(unit_of_work, source, extra_target, "owns")

    result = GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
            relation_type=KnowledgeObjectRelationType(value="uses"),
        )
    )

    assert result == (uses_relation,)


def test_connected_objects_outgoing_direction() -> None:
    unit_of_work, source, target = _create_relation_graph()
    _create_relation(unit_of_work, source, target, "uses")

    result = GetConnectedKnowledgeObjectsHandler(unit_of_work).handle(
        GetConnectedKnowledgeObjectsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
            direction=RelationDirection.OUTGOING,
        )
    )

    assert result == (target,)


def test_connected_objects_incoming_direction() -> None:
    unit_of_work, source, target = _create_relation_graph()
    _create_relation(unit_of_work, source, target, "uses")

    result = GetConnectedKnowledgeObjectsHandler(unit_of_work).handle(
        GetConnectedKnowledgeObjectsQuery(
            organization_id=target.header.organization_id,
            knowledge_object_id=target.header.id,
            direction=RelationDirection.INCOMING,
        )
    )

    assert result == (source,)


def test_connected_objects_both_direction_deduplicates_neighbours() -> None:
    unit_of_work, source, target = _create_relation_graph()
    _create_relation(unit_of_work, source, target, "uses")
    _create_relation(unit_of_work, target, source, "supports")
    _create_relation(unit_of_work, source, target, "owns")

    result = GetConnectedKnowledgeObjectsHandler(unit_of_work).handle(
        GetConnectedKnowledgeObjectsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
            direction=RelationDirection.BOTH,
        )
    )

    assert result == (target,)


def test_connected_objects_filters_by_relation_type() -> None:
    unit_of_work, source, target = _create_relation_graph()
    other_target = _create_object(unit_of_work, source.header.organization_id.value)
    _create_relation(unit_of_work, source, target, "uses")
    _create_relation(unit_of_work, source, other_target, "owns")

    result = GetConnectedKnowledgeObjectsHandler(unit_of_work).handle(
        GetConnectedKnowledgeObjectsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
            direction=RelationDirection.OUTGOING,
            relation_type=KnowledgeObjectRelationType(value="uses"),
        )
    )

    assert result == (target,)


def test_relation_traversal_ordering_is_deterministic() -> None:
    unit_of_work, source, first_target = _create_relation_graph(create_relation=False)
    second_target = _create_object(unit_of_work, source.header.organization_id.value)
    now = datetime.now(UTC)
    later_relation = _build_relation(
        relation_id=UUID("00000000-0000-0000-0000-000000000002"),
        source=source,
        target=second_target,
        relation_type="uses",
        created_at=now,
    )
    earlier_relation = _build_relation(
        relation_id=UUID("00000000-0000-0000-0000-000000000001"),
        source=source,
        target=first_target,
        relation_type="uses",
        created_at=now,
    )
    unit_of_work.relations.add(later_relation)
    unit_of_work.relations.add(earlier_relation)

    result = GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
        )
    )

    assert [relation.relation_id for relation in result] == [
        earlier_relation.relation_id,
        later_relation.relation_id,
    ]


def test_traversal_preserves_organization_isolation() -> None:
    unit_of_work, source, _target = _create_relation_graph(create_relation=False)

    with pytest.raises(KnowledgeObjectNotFound):
        GetOutgoingRelationsHandler(unit_of_work).handle(
            GetOutgoingRelationsQuery(
                organization_id=_create_object(unit_of_work, uuid4()).header.organization_id,
                knowledge_object_id=source.header.id,
            )
        )


def test_missing_root_object_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()

    with pytest.raises(KnowledgeObjectNotFound):
        GetOutgoingRelationsHandler(unit_of_work).handle(
            GetOutgoingRelationsQuery(
                organization_id=_create_object(unit_of_work, uuid4()).header.organization_id,
                knowledge_object_id=KnowledgeObjectId(value=uuid4()),
            )
        )


def test_deleted_root_object_is_rejected() -> None:
    unit_of_work, source, _target = _create_relation_graph(create_relation=False)
    DeleteKnowledgeObjectHandler(unit_of_work).handle(
        DeleteKnowledgeObjectCommand(object_id=source.header.id)
    )

    with pytest.raises(InvalidKnowledgeObjectStateTransition):
        GetOutgoingRelationsHandler(unit_of_work).handle(
            GetOutgoingRelationsQuery(
                organization_id=source.header.organization_id,
                knowledge_object_id=source.header.id,
            )
        )


def test_deleted_connected_objects_are_excluded() -> None:
    unit_of_work, source, target = _create_relation_graph()
    _create_relation(unit_of_work, source, target, "uses")
    DeleteKnowledgeObjectHandler(unit_of_work).handle(
        DeleteKnowledgeObjectCommand(object_id=target.header.id)
    )

    result = GetConnectedKnowledgeObjectsHandler(unit_of_work).handle(
        GetConnectedKnowledgeObjectsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
            direction=RelationDirection.OUTGOING,
        )
    )

    assert result == ()


def test_read_handlers_do_not_commit() -> None:
    unit_of_work, source, target = _create_relation_graph()
    _create_relation(unit_of_work, source, target, "uses")
    unit_of_work.committed = False

    GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
        )
    )

    assert unit_of_work.committed is False


def test_returned_relation_sequences_cannot_mutate_repository_state() -> None:
    unit_of_work, source, target = _create_relation_graph()
    relation = _create_relation(unit_of_work, source, target, "uses")
    result = GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
        )
    )

    with pytest.raises(AttributeError):
        result.append(relation)  # type: ignore[attr-defined]

    next_result = GetOutgoingRelationsHandler(unit_of_work).handle(
        GetOutgoingRelationsQuery(
            organization_id=source.header.organization_id,
            knowledge_object_id=source.header.id,
        )
    )
    assert next_result == (relation,)


def _create_relation_graph(
    create_relation: bool = False,
) -> tuple[InMemoryUnitOfWork, KnowledgeObject, KnowledgeObject]:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = uuid4()
    source = _create_object(unit_of_work, organization_id)
    target = _create_object(unit_of_work, organization_id)

    if create_relation:
        _create_relation(unit_of_work, source, target, "uses")

    return unit_of_work, source, target


def _create_object(
    unit_of_work: InMemoryUnitOfWork,
    organization_id,
) -> KnowledgeObject:
    return CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(
            object_type="Object",
            organization_id=organization_id,
            status=KnowledgeObjectStatus.ACTIVE,
        )
    )


def _create_relation(
    unit_of_work: InMemoryUnitOfWork,
    source: KnowledgeObject,
    target: KnowledgeObject,
    relation_type: str,
) -> KnowledgeObjectRelation:
    return CreateKnowledgeObjectRelationHandler(unit_of_work).handle(
        CreateKnowledgeObjectRelationCommand(
            source_object_id=source.header.id,
            target_object_id=target.header.id,
            relation_type=KnowledgeObjectRelationType(value=relation_type),
        )
    )


def _build_relation(
    relation_id: UUID,
    source: KnowledgeObject,
    target: KnowledgeObject,
    relation_type: str,
    created_at: datetime,
) -> KnowledgeObjectRelation:
    return KnowledgeObjectRelation(
        relation_id=relation_id,
        organization_id=source.header.organization_id,
        source_object_id=source.header.id,
        target_object_id=target.header.id,
        relation_type=KnowledgeObjectRelationType(value=relation_type),
        created_at=created_at,
    )
