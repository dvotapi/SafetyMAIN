from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId


@dataclass(frozen=True, slots=True)
class UpdateOrganizationCommand:
    organization_id: OrganizationId
    name: str
    audit_context: AuditContext | None = None
