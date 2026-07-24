from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_integrity_service import (
    AuditIntegrityService,
    order_events_by_integrity_links,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.sqlalchemy.repositories.audit_event_repository import (
    SQLAlchemyAuditEventRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


def _event(organization_id: OrganizationId) -> AuditEvent:
    return AuditEvent(
        id=AuditEventId(value=uuid4()),
        actor_user_id=UserId(value=uuid4()),
        authorization_organization_id=organization_id,
        target_organization_id=None,
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=uuid4(),
        outcome=AuditOutcome.SUCCESS,
        failure_code=None,
        metadata={"request_id": f"req-{uuid4()}"},
        occurred_at=datetime.now(UTC),
    )


@pytest.mark.db
def test_audit_integrity_concurrent_writes_same_organization(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    organization_id = OrganizationId(value=uuid4())
    barrier = Barrier(2)

    def write_one() -> AuditEventId:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        with uow:
            event = _event(organization_id)
            barrier.wait(timeout=30)
            uow.audit_events.add(event)
            uow.commit()
            return event.id

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(write_one) for _ in range(2)]
        ids = [future.result(timeout=60) for future in futures]

    with sqlalchemy_session_factory() as session:
        repository = SQLAlchemyAuditEventRepository(session)
        events = repository.list_chain_events(organization_id)
        assert len(events) == 2
        assert {event.id for event in events} == set(ids)
        genesis = [event for event in events if event.previous_integrity_hash is None]
        successors = [event for event in events if event.previous_integrity_hash is not None]
        assert len(genesis) == 1
        assert len(successors) == 1
        assert successors[0].previous_integrity_hash == genesis[0].integrity_hash
        assert genesis[0].integrity_hash != successors[0].integrity_hash
        result = AuditIntegrityService().verify_chain(
            organization_id,
            events,
            chain_head=repository.get_chain_head(organization_id),
        )
        assert result.valid is True
        ordered, fork_id = order_events_by_integrity_links(events)
        assert fork_id is None
        assert ordered is not None
        assert repository.get_latest_integrity_hash(organization_id) == ordered[-1].integrity_hash
        head = repository.get_chain_head(organization_id)
        assert head is not None
        assert head.latest_audit_event_id == ordered[-1].id


@pytest.mark.db
def test_audit_integrity_concurrent_writes_different_organizations(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    org_a = OrganizationId(value=uuid4())
    org_b = OrganizationId(value=uuid4())
    barrier = Barrier(2)

    def write(organization_id: OrganizationId) -> OrganizationId:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        with uow:
            barrier.wait(timeout=30)
            uow.audit_events.add(_event(organization_id))
            uow.commit()
        return organization_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(write, org) for org in (org_a, org_b)]
        assert {future.result(timeout=60) for future in futures} == {org_a, org_b}

    with sqlalchemy_session_factory() as session:
        repository = SQLAlchemyAuditEventRepository(session)
        for organization_id in (org_a, org_b):
            events = repository.list_chain_events(organization_id)
            assert len(events) == 1
            assert AuditIntegrityService().verify_chain(
                organization_id,
                events,
                chain_head=repository.get_chain_head(organization_id),
            ).valid
