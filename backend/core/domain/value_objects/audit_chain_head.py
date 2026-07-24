from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_integrity import (
    AuditIntegrityHash,
    AuditIntegrityVersion,
)


@dataclass(frozen=True, slots=True)
class AuditChainHead:
    """Persisted tail pointer for an organization integrity chain."""

    organization_id: OrganizationId
    latest_audit_event_id: AuditEventId
    latest_integrity_hash: AuditIntegrityHash
    integrity_version: AuditIntegrityVersion


def organization_advisory_lock_key_text(organization_id: OrganizationId) -> str:
    """Stable PostgreSQL advisory-lock input for an organization chain.

    The SQLAlchemy repository locks with:

        SELECT pg_advisory_xact_lock(hashtext(:organization_id))

    where ``organization_id`` is this canonical UUID string. Python's randomized
    ``hash()`` must never be used.
    """

    return str(organization_id.value)
