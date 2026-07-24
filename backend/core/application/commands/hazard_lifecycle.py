from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.hazard_code import HazardCode
from backend.core.domain.value_objects.safety_enums import (
    AffectedSubject,
    HazardCategory,
    HazardSource,
    SafetyDirection,
)
from backend.core.domain.value_objects.safety_ids import HazardId


@dataclass(frozen=True, slots=True)
class CreateHazardCommand:
    organization_id: OrganizationId
    actor_id: UserId
    code: HazardCode | str
    title: str
    description: str
    category: HazardCategory
    safety_directions: tuple[SafetyDirection, ...]
    source: HazardSource
    affected_subjects: tuple[AffectedSubject, ...] = ()
    location_reference: str | None = None
    process_reference: str | None = None
    equipment_reference: str | None = None
    extension_references: dict[str, str] | None = None
    identified_at: datetime | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UpdateHazardCommand:
    organization_id: OrganizationId
    hazard_id: HazardId
    actor_id: UserId
    expected_version: int
    title: str | None = None
    description: str | None = None
    category: HazardCategory | None = None
    safety_directions: tuple[SafetyDirection, ...] | None = None
    source: HazardSource | None = None
    affected_subjects: tuple[AffectedSubject, ...] | None = None
    location_reference: str | None | object = ...
    process_reference: str | None | object = ...
    equipment_reference: str | None | object = ...
    extension_references: dict[str, str] | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ActivateHazardCommand:
    organization_id: OrganizationId
    hazard_id: HazardId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ArchiveHazardCommand:
    organization_id: OrganizationId
    hazard_id: HazardId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RestoreHazardCommand:
    organization_id: OrganizationId
    hazard_id: HazardId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None
