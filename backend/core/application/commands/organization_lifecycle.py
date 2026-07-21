from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId


@dataclass(frozen=True, slots=True)
class ActivateOrganizationCommand:
    organization_id: OrganizationId
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class DeactivateOrganizationCommand:
    organization_id: OrganizationId
    authorization_organization_id: OrganizationId
    audit_context: AuditContext | None = None
