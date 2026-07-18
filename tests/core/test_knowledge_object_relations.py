from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationCommand,
)
from backend.core.application.commands.delete_knowledge_object import (
    DeleteKnowledgeObjectCommand,
)
from backend.core.application.commands.remove_knowledge_object_relation import (
    RemoveKnowledgeObjectRelationCommand,
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
from backend.core.application.handlers.remove_knowledge_object_relation import (
    RemoveKnowledgeObjectRelationHandler,
)
from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.exceptions import (
    CrossOrganizationKnowledgeObjectRelation,
    DuplicateKnowledgeObjectRelation,
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectNotFound,
    KnowledgeObjectRelationNotFound,
    SelfReferencingKnowledgeObjectRelation,
)
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_relation_type_is_normalized() -> None:
    relation_type = KnowledgeObjectRelationType(value=" Addresses ")

    assert relation_type.value == "addresses"


def test_relation_type_rejects_empty_value() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObjectRelationType(value="   ")


def test_relation_is_immutable() -> None:
    relation = KnowledgeObjectRelation(
        relation_id=uuid4(),
        organization_id=OrganizationId(value=uuid4()),
        source_object_id=KnowledgeObjectId(value=uuid4()),
        target_object_id=KnowledgeObjectId(value=uuid4()),
        relation_type=KnowledgeObjectRelationType(value="addresses"),
        created_at=datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        relation.relation_type = KnowledgeObjectRelationType(value="requires")


def test_valid_directed_relation_creation() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    relation = handler.handle(
        CreateKnowledgeObjectRelationCommand(
            source_object_id=source_object.header.id,
            target_object_id=target_object.header.id,
            relation_type=KnowledgeObjectRelationType(value="addresses"),
        )
    )

    assert relation.source_object_id == source_object.header.id
    assert relation.target_object_id == target_object.header.id
    assert relation.organization_id == source_object.header.organization_id
    assert relation.relation_type.value == "addresses"
    assert unit_of_work.relations.get(relation.relation_id) == relation
    assert unit_of_work.committed is True


def test_duplicate_directed_relation_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)
    command = CreateKnowledgeObjectRelationCommand(
        source_object_id=source_object.header.id,
        target_object_id=target_object.header.id,
        relation_type=KnowledgeObjectRelationType(value="addresses"),
    )

    handler.handle(command)

    with pytest.raises(DuplicateKnowledgeObjectRelation):
        handler.handle(command)


def test_self_referencing_relation_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, _target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(SelfReferencingKnowledgeObjectRelation):
        handler.handle(
            CreateKnowledgeObjectRelationCommand(
                source_object_id=source_object.header.id,
                target_object_id=source_object.header.id,
                relation_type=KnowledgeObjectRelationType(value="addresses"),
            )
        )


def test_cross_organization_relation_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    source_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Instruction",
            organization_id=uuid4(),
        )
    )
    target_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Risk",
            organization_id=uuid4(),
        )
    )
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(CrossOrganizationKnowledgeObjectRelation):
        handler.handle(
            CreateKnowledgeObjectRelationCommand(
                source_object_id=source_object.header.id,
                target_object_id=target_object.header.id,
                relation_type=KnowledgeObjectRelationType(value="addresses"),
            )
        )


def test_source_object_not_found_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    _source_object, target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(KnowledgeObjectNotFound):
        handler.handle(
            CreateKnowledgeObjectRelationCommand(
                source_object_id=KnowledgeObjectId(value=uuid4()),
                target_object_id=target_object.header.id,
                relation_type=KnowledgeObjectRelationType(value="addresses"),
            )
        )


def test_target_object_not_found_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, _target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(KnowledgeObjectNotFound):
        handler.handle(
            CreateKnowledgeObjectRelationCommand(
                source_object_id=source_object.header.id,
                target_object_id=KnowledgeObjectId(value=uuid4()),
                relation_type=KnowledgeObjectRelationType(value="addresses"),
            )
        )


def test_deleted_source_object_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    DeleteKnowledgeObjectHandler(unit_of_work).handle(
        DeleteKnowledgeObjectCommand(object_id=source_object.header.id)
    )
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(InvalidKnowledgeObjectStateTransition):
        handler.handle(
            CreateKnowledgeObjectRelationCommand(
                source_object_id=source_object.header.id,
                target_object_id=target_object.header.id,
                relation_type=KnowledgeObjectRelationType(value="addresses"),
            )
        )


def test_deleted_target_object_is_rejected() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    DeleteKnowledgeObjectHandler(unit_of_work).handle(
        DeleteKnowledgeObjectCommand(object_id=target_object.header.id)
    )
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(InvalidKnowledgeObjectStateTransition):
        handler.handle(
            CreateKnowledgeObjectRelationCommand(
                source_object_id=source_object.header.id,
                target_object_id=target_object.header.id,
                relation_type=KnowledgeObjectRelationType(value="addresses"),
            )
        )


def test_valid_relation_removal() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    create_handler = CreateKnowledgeObjectRelationHandler(unit_of_work)
    remove_handler = RemoveKnowledgeObjectRelationHandler(unit_of_work)
    relation = create_handler.handle(
        CreateKnowledgeObjectRelationCommand(
            source_object_id=source_object.header.id,
            target_object_id=target_object.header.id,
            relation_type=KnowledgeObjectRelationType(value="addresses"),
        )
    )

    remove_handler.handle(RemoveKnowledgeObjectRelationCommand(relation.relation_id))

    with pytest.raises(KnowledgeObjectRelationNotFound):
        unit_of_work.relations.get(relation.relation_id)


def test_missing_relation_removal_is_rejected() -> None:
    handler = RemoveKnowledgeObjectRelationHandler(InMemoryUnitOfWork())

    with pytest.raises(KnowledgeObjectRelationNotFound):
        handler.handle(RemoveKnowledgeObjectRelationCommand(uuid4()))


def test_reverse_relation_is_allowed() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    first_relation = handler.handle(
        CreateKnowledgeObjectRelationCommand(
            source_object_id=source_object.header.id,
            target_object_id=target_object.header.id,
            relation_type=KnowledgeObjectRelationType(value="uses"),
        )
    )
    reverse_relation = handler.handle(
        CreateKnowledgeObjectRelationCommand(
            source_object_id=target_object.header.id,
            target_object_id=source_object.header.id,
            relation_type=KnowledgeObjectRelationType(value="uses"),
        )
    )

    assert first_relation.relation_id != reverse_relation.relation_id


def test_unit_of_work_rollback_restores_relation_state() -> None:
    unit_of_work = InMemoryUnitOfWork()
    source_object, target_object = _create_source_and_target(unit_of_work)
    handler = CreateKnowledgeObjectRelationHandler(unit_of_work)

    with pytest.raises(RuntimeError):
        with unit_of_work:
            relation = handler.handle(
                CreateKnowledgeObjectRelationCommand(
                    source_object_id=source_object.header.id,
                    target_object_id=target_object.header.id,
                    relation_type=KnowledgeObjectRelationType(value="addresses"),
                )
            )
            raise RuntimeError("rollback")

    with pytest.raises(KnowledgeObjectRelationNotFound):
        unit_of_work.relations.get(relation.relation_id)


def _create_source_and_target(unit_of_work: InMemoryUnitOfWork):
    organization_id = uuid4()
    create_handler = CreateKnowledgeObjectHandler(unit_of_work)
    source_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Instruction",
            organization_id=organization_id,
        )
    )
    target_object = create_handler.handle(
        CreateKnowledgeObjectCommand(
            object_type="Risk",
            organization_id=organization_id,
        )
    )
    return source_object, target_object
