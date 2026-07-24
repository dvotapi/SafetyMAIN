from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_integrity_service import (
    AuditIntegrityFailureReason,
    AuditIntegrityService,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_chain_head import (
    organization_advisory_lock_key_text,
)
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.sqlalchemy.repositories.audit_event_repository import (
    SQLAlchemyAuditEventRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


def _event(organization_id: OrganizationId, *, request_id: str = "req") -> AuditEvent:
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
        metadata={"request_id": request_id},
        occurred_at=datetime.now(UTC),
    )


@pytest.mark.db
def test_advisory_lock_key_matches_postgres_hashtext(
    sqlalchemy_session: Session,
) -> None:
    organization_id = OrganizationId(value=uuid4())
    key = organization_advisory_lock_key_text(organization_id)
    value = sqlalchemy_session.scalar(text("SELECT hashtext(:key)"), {"key": key})
    assert isinstance(value, int)
    again = sqlalchemy_session.scalar(text("SELECT hashtext(:key)"), {"key": key})
    assert again == value


@pytest.mark.db
def test_audit_integrity_tamper_scenarios_detected(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    organization_id = OrganizationId(value=uuid4())
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        for index in range(3):
            uow.audit_events.add(
                _event(organization_id, request_id=f"req-{index}")
            )
        uow.commit()

    with sqlalchemy_session_factory() as session:
        repository = SQLAlchemyAuditEventRepository(session)
        events = repository.list_chain_events(organization_id)
        assert len(events) == 3
        assert AuditIntegrityService().verify_chain(
            organization_id,
            events,
            chain_head=repository.get_chain_head(organization_id),
        ).valid

        middle_id = events[1].id.value
        session.execute(
            text(
                """
                UPDATE audit_events
                SET metadata = '{"request_id":"tampered"}'::jsonb
                WHERE id = :id
                """
            ),
            {"id": middle_id},
        )
        session.commit()
        tampered_events = repository.list_chain_events(organization_id)
        result = AuditIntegrityService().verify_chain(
            organization_id,
            tampered_events,
            chain_head=repository.get_chain_head(organization_id),
        )
        assert result.valid is False
        assert result.reason is AuditIntegrityFailureReason.EVENT_HASH_MISMATCH
        assert result.first_invalid_event_id is not None
        assert result.first_invalid_event_id.value == middle_id

        # Restore metadata, then delete the final event while leaving the chain head.
        session.execute(
            text(
                """
                UPDATE audit_events
                SET metadata = '{"request_id":"req-1"}'::jsonb
                WHERE id = :id
                """
            ),
            {"id": middle_id},
        )
        final_id = events[2].id.value
        session.execute(text("DELETE FROM audit_events WHERE id = :id"), {"id": final_id})
        session.commit()
        remaining = repository.list_chain_events(organization_id)
        deleted_final = AuditIntegrityService().verify_chain(
            organization_id,
            remaining,
            chain_head=repository.get_chain_head(organization_id),
        )
        assert deleted_final.valid is False
        assert deleted_final.reason is AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH


@pytest.mark.db
def test_audit_uow_rollback_does_not_advance_chain_head(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    organization_id = OrganizationId(value=uuid4())
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        uow.audit_events.add(_event(organization_id, request_id="first"))
        uow.commit()

    with sqlalchemy_session_factory() as session:
        repository = SQLAlchemyAuditEventRepository(session)
        head_before = repository.get_chain_head(organization_id)
        assert head_before is not None

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        uow.audit_events.add(_event(organization_id, request_id="rolled-back"))
        # Intentionally leave without commit; __exit__ rolls back.
        assert uow.audit_events.get_latest_integrity_hash(organization_id) is not None

    with sqlalchemy_session_factory() as session:
        repository = SQLAlchemyAuditEventRepository(session)
        events = repository.list_chain_events(organization_id)
        assert len(events) == 1
        head_after = repository.get_chain_head(organization_id)
        assert head_after == head_before
        assert AuditIntegrityService().verify_chain(
            organization_id,
            events,
            chain_head=head_after,
        ).valid
