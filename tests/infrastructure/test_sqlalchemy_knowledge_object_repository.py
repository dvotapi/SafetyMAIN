from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObject,
    KnowledgeObjectNotFound,
    KnowledgeObjectVersionConflict,
)
from backend.core.domain.value_objects import KnowledgeObjectType, OrganizationId
from backend.core.domain.value_objects.knowledge_object_search_criteria import (
    KnowledgeObjectSearchCriteria,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyKnowledgeObjectRepository,
)


pytestmark = pytest.mark.db


@pytest.fixture(scope="module")
def database_url() -> str:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run SQLAlchemy repository tests.")

    value = os.environ.get("DATABASE_URL")
    if not value:
        pytest.skip("DATABASE_URL is required to run SQLAlchemy repository tests.")

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


def test_add_and_get_knowledge_object(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    knowledge_object = _create_knowledge_object()

    repository.add(knowledge_object)
    session.flush()

    assert repository.get(knowledge_object.header.id) == knowledge_object
    assert repository.history(knowledge_object.header.id) == ()


def test_duplicate_add_raises_domain_exception(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    knowledge_object = _create_knowledge_object()
    repository.add(knowledge_object)
    session.flush()

    with pytest.raises(DuplicateKnowledgeObject):
        repository.add(knowledge_object)


def test_missing_get_raises_domain_exception(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    missing_object = _create_knowledge_object()

    with pytest.raises(KnowledgeObjectNotFound):
        repository.get(missing_object.header.id)


def test_update_appends_previous_version_to_history(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    version_1 = _create_knowledge_object(status=KnowledgeObjectStatus.ACTIVE)
    repository.add(version_1)
    session.flush()
    version_2 = _next_version(
        version_1,
        status=KnowledgeObjectStatus.ARCHIVED,
        payload={"department": "maintenance"},
    )

    repository.update(version_2)
    session.flush()

    assert repository.get(version_1.header.id) == version_2
    assert repository.history(version_1.header.id) == (version_1,)


def test_multiple_updates_preserve_ordered_previous_versions(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    version_1 = _create_knowledge_object(status=KnowledgeObjectStatus.ACTIVE)
    repository.add(version_1)
    session.flush()
    version_2 = _next_version(version_1, status=KnowledgeObjectStatus.ARCHIVED)
    repository.update(version_2)
    session.flush()
    version_3 = _next_version(version_2, status=KnowledgeObjectStatus.DELETED)
    repository.update(version_3)
    session.flush()

    history = repository.history(version_1.header.id)

    assert history == (version_1, version_2)
    with pytest.raises(AttributeError):
        history.append(version_3)  # type: ignore[attr-defined]


def test_invalid_version_jump_raises_conflict(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    version_1 = _create_knowledge_object()
    repository.add(version_1)
    session.flush()
    version_3 = _next_version(version_1, version=3)

    with pytest.raises(KnowledgeObjectVersionConflict):
        repository.update(version_3)

    assert repository.history(version_1.header.id) == ()


def test_missing_update_raises_not_found(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)

    with pytest.raises(KnowledgeObjectNotFound):
        repository.update(_create_knowledge_object(version=2))


def test_lifecycle_statuses_are_persisted(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    active_object = _create_knowledge_object(status=KnowledgeObjectStatus.ACTIVE)
    archived_object = _create_knowledge_object(status=KnowledgeObjectStatus.ARCHIVED)
    deleted_object = _create_knowledge_object(status=KnowledgeObjectStatus.DELETED)

    for knowledge_object in (active_object, archived_object, deleted_object):
        repository.add(knowledge_object)
    session.flush()

    assert repository.get(active_object.header.id).header.status is KnowledgeObjectStatus.ACTIVE
    assert (
        repository.get(archived_object.header.id).header.status
        is KnowledgeObjectStatus.ARCHIVED
    )
    assert (
        repository.get(deleted_object.header.id).header.status
        is KnowledgeObjectStatus.DELETED
    )


def test_search_supports_filters_ordering_and_pagination(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    organization_id = OrganizationId(value=uuid4())
    other_organization_id = OrganizationId(value=uuid4())
    now = datetime.now(UTC)
    expected_first = _create_knowledge_object(
        organization_id=organization_id,
        object_type="Instruction",
        status=KnowledgeObjectStatus.ACTIVE,
        created_at=now,
        payload={"department": "production", "approved": True, "risk_level": 3},
    )
    expected_second = _create_knowledge_object(
        organization_id=organization_id,
        object_type="Instruction",
        status=KnowledgeObjectStatus.ARCHIVED,
        created_at=now + timedelta(seconds=1),
        payload={"department": "production", "approved": True, "risk_level": 3},
    )
    _add_all(
        repository,
        expected_first,
        expected_second,
        _create_knowledge_object(
            organization_id=organization_id,
            object_type="Risk",
            payload={"department": "production", "approved": True, "risk_level": 3},
        ),
        _create_knowledge_object(
            organization_id=other_organization_id,
            object_type="Instruction",
            payload={"department": "production", "approved": True, "risk_level": 3},
        ),
        _create_knowledge_object(
            organization_id=organization_id,
            object_type="Instruction",
            status=KnowledgeObjectStatus.DELETED,
            payload={"department": "production", "approved": True, "risk_level": 3},
        ),
    )
    session.flush()

    criteria = KnowledgeObjectSearchCriteria(
        organization_id=organization_id,
        object_type=KnowledgeObjectType(value="instruction"),
        metadata_equals={"department": "production", "approved": True, "risk_level": 3},
        limit=1,
        offset=1,
    )
    result = repository.search(criteria)

    assert result.total == 2
    assert result.items == (expected_second,)
    assert result.limit == 1
    assert result.offset == 1


def test_search_deleted_and_json_type_sensitivity(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    organization_id = OrganizationId(value=uuid4())
    deleted_object = _create_knowledge_object(
        organization_id=organization_id,
        status=KnowledgeObjectStatus.DELETED,
        payload={"flag": True, "risk_level": 3},
    )
    numeric_object = _create_knowledge_object(
        organization_id=organization_id,
        payload={"flag": 1, "risk_level": "3"},
    )
    _add_all(repository, deleted_object, numeric_object)
    session.flush()

    assert repository.search(
        KnowledgeObjectSearchCriteria(organization_id=organization_id, limit=100, offset=0)
    ).items == (numeric_object,)
    assert repository.search(
        KnowledgeObjectSearchCriteria(
            organization_id=organization_id,
            status=KnowledgeObjectStatus.DELETED,
            metadata_equals={"flag": True, "risk_level": 3},
            limit=100,
            offset=0,
        )
    ).items == (deleted_object,)
    assert repository.search(
        KnowledgeObjectSearchCriteria(
            organization_id=organization_id,
            metadata_equals={"flag": True},
            limit=100,
            offset=0,
        )
    ).items == ()


def test_offset_beyond_available_rows_returns_empty_page(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    organization_id = OrganizationId(value=uuid4())
    repository.add(_create_knowledge_object(organization_id=organization_id))
    session.flush()

    result = repository.search(
        KnowledgeObjectSearchCriteria(
            organization_id=organization_id,
            limit=10,
            offset=99,
        )
    )

    assert result.items == ()
    assert result.total == 1


def test_repository_does_not_commit_automatically(session: Session) -> None:
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    knowledge_object = _create_knowledge_object()
    repository.add(knowledge_object)

    assert session.in_transaction()


def test_external_rollback_removes_uncommitted_add(engine: Engine) -> None:
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    knowledge_object = _create_knowledge_object()
    repository.add(knowledge_object)
    session.flush()
    session.rollback()
    session.close()

    verification_session = session_factory()
    verification_repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
    with pytest.raises(KnowledgeObjectNotFound):
        verification_repository.get(knowledge_object.header.id)
    verification_session.close()


def test_external_rollback_removes_update_and_history(engine: Engine) -> None:
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    repository = SQLAlchemyKnowledgeObjectRepository(session)
    version_1 = _create_knowledge_object()
    repository.add(version_1)
    session.commit()
    version_2 = _next_version(version_1)
    repository.update(version_2)
    session.flush()
    session.rollback()
    session.close()

    verification_session = session_factory()
    verification_repository = SQLAlchemyKnowledgeObjectRepository(verification_session)
    assert verification_repository.get(version_1.header.id) == version_1
    assert verification_repository.history(version_1.header.id) == ()
    verification_session.close()


def _add_all(
    repository: SQLAlchemyKnowledgeObjectRepository,
    *knowledge_objects: KnowledgeObject,
) -> None:
    for knowledge_object in knowledge_objects:
        repository.add(knowledge_object)


def _create_knowledge_object(
    *,
    object_id=None,
    organization_id: OrganizationId | None = None,
    object_type: str = "Instruction",
    status: KnowledgeObjectStatus = KnowledgeObjectStatus.ACTIVE,
    version: int = 1,
    created_at: datetime | None = None,
    payload: dict[str, object] | None = None,
) -> KnowledgeObject:
    now = created_at or datetime.now(UTC)
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=object_id or uuid4(),
            object_type=object_type,
            organization_id=organization_id or uuid4(),
            status=status,
            version=version,
            created_at=now,
            updated_at=now,
        ),
        payload=payload or {},
    )


def _next_version(
    knowledge_object: KnowledgeObject,
    *,
    status: KnowledgeObjectStatus | None = None,
    version: int | None = None,
    payload: dict[str, object] | None = None,
) -> KnowledgeObject:
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=knowledge_object.header.id,
            object_type=knowledge_object.header.object_type,
            organization_id=knowledge_object.header.organization_id,
            status=status or knowledge_object.header.status,
            version=version or knowledge_object.header.version.value + 1,
            created_at=knowledge_object.header.created_at,
            updated_at=datetime.now(UTC),
        ),
        payload=payload or knowledge_object.payload,
    )
