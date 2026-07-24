from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_event_canonicalizer import (
    resolve_audit_chain_organization_id,
)
from backend.core.domain.services.audit_integrity_service import AuditIntegrityService
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def _legacy_domain_events() -> list[AuditEvent]:
    org_a = OrganizationId(value=UUID("11111111-1111-4111-8111-111111111111"))
    org_b = OrganizationId(value=UUID("22222222-2222-4222-8222-222222222222"))
    actor = UserId(value=UUID("33333333-3333-4333-8333-333333333333"))
    base = datetime(2026, 7, 24, 10, 0, 0, tzinfo=UTC)
    specs = [
        (
            UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"),
            org_a,
            AuditAction.USER_CREATE,
            base,
            {},
        ),
        (
            UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2"),
            org_a,
            AuditAction.USER_UPDATE,
            base,  # equal timestamp; id ordering decides chain order
            {"request_id": "same-second"},
        ),
        (
            UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1"),
            org_b,
            AuditAction.AUTHENTICATION_LOGIN_FAILED,
            base + timedelta(seconds=1),
            {"request_id": "auth-fail", "client_ip": "203.0.113.10"},
        ),
        (
            UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2"),
            org_b,
            AuditAction.AUTHORIZATION_PERMISSION_DENIED,
            base + timedelta(seconds=2),
            {
                "required_permission": "audit:read",
                "http_method": "GET",
                "route_template": "/api/v1/admin/audit-events",
            },
        ),
    ]
    events: list[AuditEvent] = []
    for event_id, org, action, occurred_at, metadata in specs:
        auth_org = None if action.value.startswith("authentication.") else org
        events.append(
            AuditEvent(
                id=AuditEventId(value=event_id),
                actor_user_id=None if action is AuditAction.AUTHENTICATION_LOGIN_FAILED else actor,
                authorization_organization_id=auth_org,
                target_organization_id=org if auth_org is None else None,
                action=action,
                resource_type=(
                    AuditResourceType.SESSION
                    if action.value.startswith("authentication.")
                    else AuditResourceType.USER
                    if action.value.startswith("user.")
                    else AuditResourceType.AUDIT_EVENT
                ),
                resource_id=None,
                outcome=(
                    AuditOutcome.FAILURE
                    if action
                    in {
                        AuditAction.AUTHENTICATION_LOGIN_FAILED,
                        AuditAction.AUTHORIZATION_PERMISSION_DENIED,
                    }
                    else AuditOutcome.SUCCESS
                ),
                failure_code=(
                    "invalid_credentials"
                    if action is AuditAction.AUTHENTICATION_LOGIN_FAILED
                    else "permission_denied"
                    if action is AuditAction.AUTHORIZATION_PERMISSION_DENIED
                    else None
                ),
                metadata=metadata,
                occurred_at=occurred_at,
            )
        )
    return events


def _backfill_hashes(events: list[AuditEvent]) -> dict[UUID, tuple[str | None, str, int]]:
    integrity = AuditIntegrityService()
    grouped: dict[OrganizationId, list[AuditEvent]] = {}
    for event in events:
        grouped.setdefault(resolve_audit_chain_organization_id(event), []).append(event)
    results: dict[UUID, tuple[str | None, str, int]] = {}
    for chain_events in grouped.values():
        chain_events.sort(key=lambda item: (item.occurred_at, item.id.value))
        previous = None
        for event in chain_events:
            finalized = integrity.finalize_event(event, previous)
            assert finalized.integrity_hash is not None
            assert finalized.integrity_version is not None
            results[finalized.id.value] = (
                finalized.previous_integrity_hash.value
                if finalized.previous_integrity_hash
                else None,
                finalized.integrity_hash.value,
                finalized.integrity_version.value,
            )
            previous = finalized.integrity_hash
    return results


def test_deterministic_integrity_backfill_is_idempotent_across_runs() -> None:
    events = _legacy_domain_events()
    first = _backfill_hashes(events)
    second = _backfill_hashes(list(reversed(events)))
    assert first == second
    assert len(first) == 4


@pytest.mark.db
def test_migration_0007_deterministic_backfill_matches_runtime_algorithm() -> None:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run PostgreSQL tests.")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.fail(
            "SAFETYMAIN_RUN_DB_TESTS=1 requires DATABASE_URL; refusing to silently skip."
        )

    expected = _backfill_hashes(_legacy_domain_events())
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    engine = create_engine(database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "0006_audit_investigation_indexes")

    with engine.begin() as connection:
        for event in _legacy_domain_events():
            connection.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        id, actor_user_id, authorization_organization_id,
                        target_organization_id, action, resource_type, resource_id,
                        outcome, failure_code, metadata, occurred_at
                    ) VALUES (
                        :id, :actor, :auth_org, :target_org, :action, :resource_type,
                        :resource_id, :outcome, :failure_code, CAST(:metadata AS jsonb),
                        :occurred_at
                    )
                    """
                ),
                {
                    "id": event.id.value,
                    "actor": event.actor_user_id.value if event.actor_user_id else None,
                    "auth_org": (
                        event.authorization_organization_id.value
                        if event.authorization_organization_id
                        else None
                    ),
                    "target_org": (
                        event.target_organization_id.value
                        if event.target_organization_id
                        else None
                    ),
                    "action": event.action.value,
                    "resource_type": event.resource_type.value,
                    "resource_id": event.resource_id,
                    "outcome": event.outcome.value,
                    "failure_code": event.failure_code,
                    "metadata": __import__("json").dumps(event.metadata),
                    "occurred_at": event.occurred_at,
                },
            )

    command.upgrade(config, "0007_audit_event_integrity_chain")

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, previous_integrity_hash, integrity_hash, integrity_version
                FROM audit_events
                """
            )
        ).mappings().all()
        actual = {
            row["id"]: (
                row["previous_integrity_hash"],
                row["integrity_hash"],
                row["integrity_version"],
            )
            for row in rows
        }
        assert actual == expected

    command.downgrade(config, "base")
    engine.dispose()
