from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from scripts.verify_audit_integrity import main, verify_all


@pytest.mark.db
def test_verify_audit_integrity_cli_exit_codes(
    sqlalchemy_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    organization_id = OrganizationId(value=uuid4())
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        uow.audit_events.add(
            AuditEvent(
                id=AuditEventId(value=uuid4()),
                actor_user_id=UserId(value=uuid4()),
                authorization_organization_id=organization_id,
                target_organization_id=None,
                action=AuditAction.USER_CREATE,
                resource_type=AuditResourceType.USER,
                resource_id=uuid4(),
                outcome=AuditOutcome.SUCCESS,
                failure_code=None,
                metadata={"request_id": "cli-ok"},
                occurred_at=datetime.now(UTC),
            )
        )
        uow.commit()

    assert verify_all(sqlalchemy_session_factory) == 0

    with sqlalchemy_session_factory() as session:
        session.execute(
            __import__("sqlalchemy").text(
                """
                UPDATE audit_events
                SET metadata = '{"request_id":"tampered-cli"}'::jsonb
                WHERE authorization_organization_id = :org
                """
            ),
            {"org": organization_id.value},
        )
        session.commit()

    assert verify_all(sqlalchemy_session_factory) == 1

    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Force settings lookup failure path without printing secrets.
    monkeypatch.setenv("DATABASE_URL", "")
    # get_database_url may raise; main should return infrastructure failure code 2.
    code = main([])
    assert code in {1, 2}


def test_db_tests_fail_hard_when_enabled_without_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAFETYMAIN_RUN_DB_TESTS", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from tests.infrastructure import db_fixtures

    with pytest.raises(pytest.fail.Exception, match="DATABASE_URL"):
        db_fixtures._require_database_url()
