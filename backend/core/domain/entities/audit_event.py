from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType

ALLOWED_METADATA_KEYS = frozenset(
    {
        "changed_fields",
        "previous_role",
        "new_role",
        "previous_status",
        "new_status",
        "expiration_refreshed",
        "membership_id",
    }
)


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: AuditEventId
    actor_user_id: UserId | None = None
    authorization_organization_id: OrganizationId | None = None
    target_organization_id: OrganizationId | None = None
    action: AuditAction
    resource_type: AuditResourceType
    resource_id: UUID | None = None
    outcome: AuditOutcome
    failure_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        unknown_keys = set(value) - ALLOWED_METADATA_KEYS
        if unknown_keys:
            raise ValueError(f"Unsupported audit metadata keys: {sorted(unknown_keys)}")
        return value

    @field_validator("failure_code")
    @classmethod
    def validate_failure_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Audit failure code must not be empty.")
        return normalized
