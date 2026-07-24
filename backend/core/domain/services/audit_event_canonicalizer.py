from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.security_events.registry import security_event_descriptor_for
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_integrity import (
    CURRENT_AUDIT_INTEGRITY_VERSION,
    PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID,
    AuditIntegrityVersion,
)


class AuditCanonicalizationError(ValueError):
    """Raised when an audit event cannot be deterministically canonicalized."""


def resolve_audit_chain_organization_id(event: AuditEvent) -> OrganizationId:
    """Resolve the integrity chain partition for an audit event.

    Preference order:
    1. authorization_organization_id
    2. target_organization_id
    3. platform sentinel (org-less authentication events)
    """

    if event.authorization_organization_id is not None:
        return event.authorization_organization_id
    if event.target_organization_id is not None:
        return event.target_organization_id
    return OrganizationId(value=PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID)


def canonicalize_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AuditCanonicalizationError("Timestamps must be timezone-aware.")
    utc_value = value.astimezone(UTC)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def canonicalize_metadata(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AuditCanonicalizationError("Non-finite floating-point values are unsupported.")
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return canonicalize_datetime(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [canonicalize_metadata(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise AuditCanonicalizationError("Metadata mapping keys must be strings.")
            normalized[key] = canonicalize_metadata(item)
        return {key: normalized[key] for key in sorted(normalized)}
    raise AuditCanonicalizationError(
        f"Unsupported metadata value type: {type(value).__name__}."
    )


def build_canonical_audit_payload(
    event: AuditEvent,
    *,
    integrity_version: AuditIntegrityVersion = CURRENT_AUDIT_INTEGRITY_VERSION,
) -> dict[str, Any]:
    descriptor = security_event_descriptor_for(event.action.value)
    request_id = event.metadata.get("request_id")
    return {
        "action": event.action.value,
        "actor_user_id": (
            str(event.actor_user_id.value) if event.actor_user_id is not None else None
        ),
        "audit_event_id": str(event.id.value),
        "authorization_organization_id": (
            str(event.authorization_organization_id.value)
            if event.authorization_organization_id is not None
            else None
        ),
        "event_category": descriptor.category.value if descriptor is not None else None,
        "event_name": event.action.value,
        "failure_code": event.failure_code,
        "integrity_version": integrity_version.value,
        "metadata": canonicalize_metadata(event.metadata),
        "occurred_at": canonicalize_datetime(event.occurred_at),
        "outcome": event.outcome.value,
        "request_id": request_id if isinstance(request_id, str) else None,
        "resource_id": str(event.resource_id) if event.resource_id is not None else None,
        "resource_type": event.resource_type.value,
        "severity": (
            descriptor.default_security_significance.value
            if descriptor is not None and descriptor.default_security_significance is not None
            else None
        ),
        "target_organization_id": (
            str(event.target_organization_id.value)
            if event.target_organization_id is not None
            else None
        ),
    }


def canonical_audit_event_bytes(
    event: AuditEvent,
    *,
    previous_integrity_hash: str | None,
    integrity_version: AuditIntegrityVersion = CURRENT_AUDIT_INTEGRITY_VERSION,
) -> bytes:
    payload = {
        "event": build_canonical_audit_payload(event, integrity_version=integrity_version),
        "integrity_version": integrity_version.value,
        "previous_integrity_hash": previous_integrity_hash,
    }
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return serialized.encode("utf-8")
