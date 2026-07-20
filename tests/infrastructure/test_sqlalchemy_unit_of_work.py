from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import (
    KnowledgeObjectNotFound,
    KnowledgeObjectRelationNotFound,
)
from backend.core.domain.value_objects import (
    KnowledgeObjectRelationType,
    OrganizationId,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyKnowledgeObjectRelationRepository,
    SQLAlchemyKnowledgeObjectRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


pytestmark = pytest.mark.db
pytest_plugins = ("tests.infrastructure.db_fixtures",)


def test_repositories_share_one_session(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        assert unit_of_work.knowledge_objects._session is unit_of_work.session
        assert unit_of_work.relations._session is unit_of_work.session
        assert unit_of_work.knowledge_objects._session is unit_of_work.relations._session


def test_commit_persists_objects_and_relations(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    source = _create_object()
    target = _create_object(organization_id=source.header.organization_id)
    relation = _create_relation(source=source, target=target)

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.knowledge_objects.add(source)
        unit_of_work.knowledge_objects.add(target)
        unit_of_work.relations.add(relation)
        unit_of_work.commit()

    verification_session = sqlalchemy_session_factory()
    try:
        object_repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
        relation_repository = SQLAlchemyKnowledgeObjectRelationRepository(
            verification_session
        )
        assert object_repository.get(source.header.id) == source
        assert object_repository.get(target.header.id) == target
        assert relation_repository.get(relation.relation_id) == relation
    finally:
        verification_session.close()


def test_exception_rolls_back_objects_and_relations(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    source = _create_object()
    target = _create_object(organization_id=source.header.organization_id)
    relation = _create_relation(source=source, target=target)

    with pytest.raises(RuntimeError):
        with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
            unit_of_work.knowledge_objects.add(source)
            unit_of_work.knowledge_objects.add(target)
            unit_of_work.relations.add(relation)
            raise RuntimeError("rollback")

    verification_session = sqlalchemy_session_factory()
    try:
        object_repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
        relation_repository = SQLAlchemyKnowledgeObjectRelationRepository(
            verification_session
        )
        with pytest.raises(KnowledgeObjectNotFound):
            object_repository.get(source.header.id)
        with pytest.raises(KnowledgeObjectRelationNotFound):
            relation_repository.get(relation.relation_id)
    finally:
        verification_session.close()


def test_update_history_rolls_back_on_exception(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    version_1 = _create_object()
    version_2 = _next_version(version_1)
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.knowledge_objects.add(version_1)
        unit_of_work.commit()

    with pytest.raises(RuntimeError):
        with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
            unit_of_work.knowledge_objects.update(version_2)
            raise RuntimeError("rollback")

    verification_session = sqlalchemy_session_factory()
    try:
        repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
        assert repository.get(version_1.header.id) == version_1
        assert repository.history(version_1.header.id) == ()
    finally:
        verification_session.close()


def test_remove_relation_rolls_back_on_exception(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    source = _create_object()
    target = _create_object(organization_id=source.header.organization_id)
    relation = _create_relation(source=source, target=target)
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.knowledge_objects.add(source)
        unit_of_work.knowledge_objects.add(target)
        unit_of_work.relations.add(relation)
        unit_of_work.commit()

    with pytest.raises(RuntimeError):
        with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
            unit_of_work.relations.remove(relation.relation_id)
            raise RuntimeError("rollback")

    verification_session = sqlalchemy_session_factory()
    try:
        repository = SQLAlchemyKnowledgeObjectRelationRepository(verification_session)
        assert repository.get(relation.relation_id) == relation
    finally:
        verification_session.close()


def test_exit_without_commit_rolls_back(sqlalchemy_session_factory: sessionmaker[Session]) -> None:
    knowledge_object = _create_object()

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.knowledge_objects.add(knowledge_object)

    verification_session = sqlalchemy_session_factory()
    try:
        repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
        with pytest.raises(KnowledgeObjectNotFound):
            repository.get(knowledge_object.header.id)
    finally:
        verification_session.close()


def test_session_is_closed_after_context_exit(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    unit_of_work = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with unit_of_work:
        _session = unit_of_work.session

    with pytest.raises(RuntimeError, match="not been entered"):
        unit_of_work.session


def test_double_rollback_does_not_fail(sqlalchemy_session_factory: sessionmaker[Session]) -> None:
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.rollback()
        unit_of_work.rollback()


def test_double_commit_is_noop(sqlalchemy_session_factory: sessionmaker[Session]) -> None:
    knowledge_object = _create_object()

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.knowledge_objects.add(knowledge_object)
        unit_of_work.commit()
        unit_of_work.commit()

    verification_session = sqlalchemy_session_factory()
    try:
        repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
        assert repository.get(knowledge_object.header.id) == knowledge_object
    finally:
        verification_session.close()


def test_repository_flushes_do_not_commit(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    knowledge_object = _create_object()

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as unit_of_work:
        unit_of_work.knowledge_objects.add(knowledge_object)
        unit_of_work.session.flush()
        unit_of_work.rollback()

    verification_session = sqlalchemy_session_factory()
    try:
        repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
        with pytest.raises(KnowledgeObjectNotFound):
            repository.get(knowledge_object.header.id)
    finally:
        verification_session.close()


def _create_object(
    organization_id: OrganizationId | None = None,
) -> KnowledgeObject:
    now = datetime.now(UTC)
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Object",
            organization_id=organization_id or uuid4(),
            status=KnowledgeObjectStatus.ACTIVE,
            version=1,
            created_at=now,
            updated_at=now,
        ),
        payload={},
    )


def _next_version(knowledge_object: KnowledgeObject) -> KnowledgeObject:
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=knowledge_object.header.id,
            object_type=knowledge_object.header.object_type,
            organization_id=knowledge_object.header.organization_id,
            status=KnowledgeObjectStatus.ARCHIVED,
            version=knowledge_object.header.version.value + 1,
            created_at=knowledge_object.header.created_at,
            updated_at=datetime.now(UTC),
        ),
        payload=knowledge_object.payload,
    )


def _create_relation(
    source: KnowledgeObject,
    target: KnowledgeObject,
) -> KnowledgeObjectRelation:
    return KnowledgeObjectRelation(
        relation_id=uuid4(),
        organization_id=source.header.organization_id,
        source_object_id=source.header.id,
        target_object_id=target.header.id,
        relation_type=KnowledgeObjectRelationType(value="uses"),
        created_at=datetime.now(UTC),
    )
