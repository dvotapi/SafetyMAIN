"""Add tamper-evident audit integrity chain columns and chain heads.

Backfill strategy:
1. Add nullable integrity columns and audit_chain_heads.
2. Deterministically backfill each chain partition (authorization org, else target,
   else platform sentinel) in ascending (occurred_at, id) order using the same
   canonical SHA-256 algorithm as runtime.
3. Enforce non-null integrity_hash/integrity_version for all rows.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0007_audit_event_integrity_chain"
down_revision = "0006_audit_investigation_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_events",
        sa.Column("previous_integrity_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "audit_events",
        sa.Column("integrity_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "audit_events",
        sa.Column("integrity_version", sa.Integer(), nullable=True),
    )
    op.create_table(
        "audit_chain_heads",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("latest_audit_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("latest_integrity_hash", sa.String(length=64), nullable=False),
        sa.Column("integrity_version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("organization_id"),
    )
    op.create_check_constraint(
        "ck_audit_events_integrity_hash_len",
        "audit_events",
        "integrity_hash IS NULL OR char_length(integrity_hash) = 64",
    )
    op.create_check_constraint(
        "ck_audit_events_previous_integrity_hash_len",
        "audit_events",
        "previous_integrity_hash IS NULL OR char_length(previous_integrity_hash) = 64",
    )
    op.create_check_constraint(
        "ck_audit_events_integrity_version_positive",
        "audit_events",
        "integrity_version IS NULL OR integrity_version > 0",
    )

    _backfill_integrity_chains()

    op.alter_column("audit_events", "integrity_hash", nullable=False)
    op.alter_column("audit_events", "integrity_version", nullable=False)


def downgrade() -> None:
    op.drop_constraint("ck_audit_events_integrity_version_positive", "audit_events", type_="check")
    op.drop_constraint(
        "ck_audit_events_previous_integrity_hash_len",
        "audit_events",
        type_="check",
    )
    op.drop_constraint("ck_audit_events_integrity_hash_len", "audit_events", type_="check")
    op.drop_table("audit_chain_heads")
    op.drop_column("audit_events", "integrity_version")
    op.drop_column("audit_events", "integrity_hash")
    op.drop_column("audit_events", "previous_integrity_hash")


def _backfill_integrity_chains() -> None:
    from backend.core.domain.entities.audit_event import AuditEvent
    from backend.core.domain.services.audit_event_canonicalizer import (
        resolve_audit_chain_organization_id,
    )
    from backend.core.domain.services.audit_integrity_service import (
        AuditIntegrityService,
    )
    from backend.core.domain.value_objects import OrganizationId, UserId
    from backend.core.domain.value_objects.audit_action import AuditAction
    from backend.core.domain.value_objects.audit_event_id import AuditEventId
    from backend.core.domain.value_objects.audit_outcome import AuditOutcome
    from backend.core.domain.value_objects.audit_resource_type import AuditResourceType

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT
                id,
                actor_user_id,
                authorization_organization_id,
                target_organization_id,
                action,
                resource_type,
                resource_id,
                outcome,
                failure_code,
                metadata,
                occurred_at
            FROM audit_events
            ORDER BY occurred_at ASC, id ASC
            """
        )
    ).mappings().all()

    integrity = AuditIntegrityService()
    grouped: dict[object, list[object]] = defaultdict(list)
    domain_events: list[AuditEvent] = []

    for row in rows:
        event = AuditEvent(
            id=AuditEventId(value=row["id"]),
            actor_user_id=(
                UserId(value=row["actor_user_id"]) if row["actor_user_id"] else None
            ),
            authorization_organization_id=(
                OrganizationId(value=row["authorization_organization_id"])
                if row["authorization_organization_id"]
                else None
            ),
            target_organization_id=(
                OrganizationId(value=row["target_organization_id"])
                if row["target_organization_id"]
                else None
            ),
            action=AuditAction(row["action"]),
            resource_type=AuditResourceType(row["resource_type"]),
            resource_id=row["resource_id"],
            outcome=AuditOutcome(row["outcome"]),
            failure_code=row["failure_code"],
            metadata=dict(row["metadata"] or {}),
            occurred_at=row["occurred_at"],
        )
        domain_events.append(event)
        grouped[resolve_audit_chain_organization_id(event)].append(event)

    now = datetime.now(UTC)
    for chain_org, events in grouped.items():
        previous = None
        last_finalized = None
        for event in events:
            finalized = integrity.finalize_event(event, previous)
            assert finalized.integrity_hash is not None
            assert finalized.integrity_version is not None
            connection.execute(
                sa.text(
                    """
                    UPDATE audit_events
                    SET
                        previous_integrity_hash = :previous_integrity_hash,
                        integrity_hash = :integrity_hash,
                        integrity_version = :integrity_version
                    WHERE id = :id
                    """
                ),
                {
                    "id": finalized.id.value,
                    "previous_integrity_hash": (
                        finalized.previous_integrity_hash.value
                        if finalized.previous_integrity_hash
                        else None
                    ),
                    "integrity_hash": finalized.integrity_hash.value,
                    "integrity_version": finalized.integrity_version.value,
                },
            )
            previous = finalized.integrity_hash
            last_finalized = finalized

        if last_finalized is not None and last_finalized.integrity_hash is not None:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO audit_chain_heads (
                        organization_id,
                        latest_audit_event_id,
                        latest_integrity_hash,
                        integrity_version,
                        updated_at
                    ) VALUES (
                        :organization_id,
                        :latest_audit_event_id,
                        :latest_integrity_hash,
                        :integrity_version,
                        :updated_at
                    )
                    """
                ),
                {
                    "organization_id": chain_org.value,
                    "latest_audit_event_id": last_finalized.id.value,
                    "latest_integrity_hash": last_finalized.integrity_hash.value,
                    "integrity_version": last_finalized.integrity_version.value,
                    "updated_at": now,
                },
            )
