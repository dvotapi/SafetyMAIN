from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObjectRelation,
    KnowledgeObjectRelationNotFound,
    SelfReferencingKnowledgeObjectRelation,
)
from backend.core.domain.value_objects import KnowledgeObjectRelationType, OrganizationId
from backend.core.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyKnowledgeObjectRelationRepository,
    SQLAlchemyKnowledgeObjectRepository,
)


pytestmark = pytest.mark.db


@pytest.fixture(scope="module")
def database_url() -> str:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run SQLAlchemy relation tests.")

    value = os.environ.get("DATABASE_URL")
    if not value:
        pytest.skip("DATABASE_URL is required to run SQLAlchemy relation tests.")

    return value


@pytest.fixture()
def engine(database_url: str) -> Iterator[Engine]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        yield engine
    finally:
        engine.dispose()
        command.downgrade(config, "base")


@pytest.fixture()
def session(engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_add_and_get_relation(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)

    relation_repository.add(relation)
    session.flush()

    assert relation_repository.get(relation.relation_id) == relation


def test_repository_does_not_commit_automatically(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)

    relation_repository.add(_create_relation(source=source, target=target))

    assert session.in_transaction()


def test_duplicate_directed_relation_raises_domain_exception(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target, relation_type="uses")
    duplicate = _create_relation(source=source, target=target, relation_type="uses")
    relation_repository.add(relation)
    session.flush()

    with pytest.raises(DuplicateKnowledgeObjectRelation):
        relation_repository.add(duplicate)


def test_reverse_relation_is_allowed(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target, relation_type="uses")
    reverse_relation = _create_relation(source=target, target=source, relation_type="uses")

    relation_repository.add(relation)
    relation_repository.add(reverse_relation)
    session.flush()

    assert relation_repository.get(relation.relation_id) == relation
    assert relation_repository.get(reverse_relation.relation_id) == reverse_relation


def test_duplicate_relation_id_raises_domain_exception(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation_id = uuid4()
    relation = _create_relation(source=source, target=target, relation_id=relation_id)
    duplicate_id_relation = _create_relation(
        source=target,
        target=source,
        relation_id=relation_id,
    )
    relation_repository.add(relation)
    session.flush()

    with pytest.raises(DuplicateKnowledgeObjectRelation):
        relation_repository.add(duplicate_id_relation)


def test_self_reference_raises_domain_exception(session: Session) -> None:
    relation_repository, source, _target = _create_repository_with_objects(session)

    with pytest.raises(SelfReferencingKnowledgeObjectRelation):
        relation_repository.add(_create_relation(source=source, target=source))


def test_missing_relation_raises_not_found(session: Session) -> None:
    relation_repository, _source, _target = _create_repository_with_objects(session)

    with pytest.raises(KnowledgeObjectRelationNotFound):
        relation_repository.get(uuid4())


def test_valid_relation_removal(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()

    relation_repository.remove(relation.relation_id)
    session.flush()

    with pytest.raises(KnowledgeObjectRelationNotFound):
        relation_repository.get(relation.relation_id)


def test_missing_relation_removal_raises_not_found(session: Session) -> None:
    relation_repository, _source, _target = _create_repository_with_objects(session)

    with pytest.raises(KnowledgeObjectRelationNotFound):
        relation_repository.remove(uuid4())


def test_removing_relation_does_not_remove_connected_objects(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    object_repository = SQLAlchemyKnowledgeObjectRepository(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()

    relation_repository.remove(relation.relation_id)
    session.flush()

    assert object_repository.get(source.header.id) == source
    assert object_repository.get(target.header.id) == target


def test_removing_one_relation_does_not_remove_other_relations(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    first_relation = _create_relation(source=source, target=target, relation_type="uses")
    second_relation = _create_relation(
        source=source,
        target=target,
        relation_type="supports",
    )
    relation_repository.add(first_relation)
    relation_repository.add(second_relation)
    session.flush()

    relation_repository.remove(first_relation.relation_id)
    session.flush()

    assert relation_repository.get(second_relation.relation_id) == second_relation


def test_external_rollback_restores_uncommitted_removal(engine: Engine) -> None:
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.commit()

    relation_repository.remove(relation.relation_id)
    session.flush()
    session.rollback()
    session.close()

    verification_session = session_factory()
    verification_repository = SQLAlchemyKnowledgeObjectRelationRepository(
        verification_session
    )
    assert verification_repository.get(relation.relation_id) == relation
    verification_session.close()


def test_exists_semantics(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target, relation_type="uses")
    relation_repository.add(relation)
    session.flush()

    assert relation_repository.exists(
        organization_id=relation.organization_id,
        source_object_id=relation.source_object_id,
        target_object_id=relation.target_object_id,
        relation_type=relation.relation_type,
    )
    assert not relation_repository.exists(
        organization_id=relation.organization_id,
        source_object_id=relation.target_object_id,
        target_object_id=relation.source_object_id,
        relation_type=relation.relation_type,
    )
    assert not relation_repository.exists(
        organization_id=relation.organization_id,
        source_object_id=relation.source_object_id,
        target_object_id=relation.target_object_id,
        relation_type=KnowledgeObjectRelationType(value="owns"),
    )
    assert not relation_repository.exists(
        organization_id=OrganizationId(value=uuid4()),
        source_object_id=relation.source_object_id,
        target_object_id=relation.target_object_id,
        relation_type=relation.relation_type,
    )


def test_outgoing_traversal(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()

    assert relation_repository.outgoing(
        organization_id=relation.organization_id,
        source_object_id=source.header.id,
    ) == (relation,)
    assert relation_repository.outgoing(
        organization_id=relation.organization_id,
        source_object_id=source.header.id,
        relation_type=KnowledgeObjectRelationType(value="missing"),
    ) == ()


def test_incoming_traversal(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()

    assert relation_repository.incoming(
        organization_id=relation.organization_id,
        target_object_id=target.header.id,
    ) == (relation,)
    assert relation_repository.incoming(
        organization_id=relation.organization_id,
        target_object_id=target.header.id,
        relation_type=KnowledgeObjectRelationType(value="missing"),
    ) == ()


def test_traversal_ordering_is_deterministic(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    now = datetime.now(UTC)
    later_relation = _create_relation(
        source=source,
        target=target,
        relation_id=UUID("00000000-0000-0000-0000-000000000002"),
        created_at=now,
        relation_type="uses",
    )
    earlier_relation = _create_relation(
        source=source,
        target=target,
        relation_id=UUID("00000000-0000-0000-0000-000000000001"),
        created_at=now,
        relation_type="owns",
    )
    relation_repository.add(later_relation)
    relation_repository.add(earlier_relation)
    session.flush()

    assert relation_repository.outgoing(
        organization_id=source.header.organization_id,
        source_object_id=source.header.id,
    ) == (earlier_relation, later_relation)


def test_traversal_results_are_immutable(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()
    result = relation_repository.outgoing(
        organization_id=source.header.organization_id,
        source_object_id=source.header.id,
    )

    with pytest.raises(AttributeError):
        result.append(relation)  # type: ignore[attr-defined]


def test_traversal_preserves_organization_isolation(session: Session) -> None:
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()

    assert relation_repository.outgoing(
        organization_id=OrganizationId(value=uuid4()),
        source_object_id=source.header.id,
    ) == ()


def test_external_rollback_removes_uncommitted_add(engine: Engine) -> None:
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    relation_repository, source, target = _create_repository_with_objects(session)
    relation = _create_relation(source=source, target=target)
    relation_repository.add(relation)
    session.flush()
    session.rollback()
    session.close()

    verification_session = session_factory()
    verification_repository = SQLAlchemyKnowledgeObjectRelationRepository(
        verification_session
    )
    with pytest.raises(KnowledgeObjectRelationNotFound):
        verification_repository.get(relation.relation_id)
    verification_session.close()


def _create_repository_with_objects(
    session: Session,
) -> tuple[SQLAlchemyKnowledgeObjectRelationRepository, KnowledgeObject, KnowledgeObject]:
    object_repository = SQLAlchemyKnowledgeObjectRepository(session)
    organization_id = OrganizationId(value=uuid4())
    source = _create_object(organization_id=organization_id)
    target = _create_object(organization_id=organization_id)
    object_repository.add(source)
    object_repository.add(target)
    session.flush()
    return SQLAlchemyKnowledgeObjectRelationRepository(session), source, target


def _create_object(organization_id: OrganizationId) -> KnowledgeObject:
    now = datetime.now(UTC)
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Object",
            organization_id=organization_id,
            status=KnowledgeObjectStatus.ACTIVE,
            version=1,
            created_at=now,
            updated_at=now,
        ),
        payload={},
    )


def _create_relation(
    *,
    source: KnowledgeObject,
    target: KnowledgeObject,
    relation_id=None,
    relation_type: str = "uses",
    created_at: datetime | None = None,
) -> KnowledgeObjectRelation:
    return KnowledgeObjectRelation(
        relation_id=relation_id or uuid4(),
        organization_id=source.header.organization_id,
        source_object_id=source.header.id,
        target_object_id=target.header.id,
        relation_type=KnowledgeObjectRelationType(value=relation_type),
        created_at=created_at or datetime.now(UTC),
    )
