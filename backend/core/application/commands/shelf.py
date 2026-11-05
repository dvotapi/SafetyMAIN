"""Commands of the document shelf (TASK-P11-012 §2.5)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_values import SlotLegalBasis


@dataclass(frozen=True, slots=True)
class CreateShelfSectionCommand:
    organization_id: OrganizationId
    actor_id: UserId
    code: str
    number: int
    title: str
    safety_domain: SafetyDomain
    subsections: tuple[tuple[str, str], ...] = ()
    """``(code, title)`` pairs in shelf order."""
    section_id: ShelfSectionId | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RenameShelfSectionCommand:
    organization_id: OrganizationId
    section_id: ShelfSectionId
    actor_id: UserId
    expected_version: int
    title: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class AddShelfSubsectionCommand:
    organization_id: OrganizationId
    section_id: ShelfSectionId
    actor_id: UserId
    expected_version: int
    code: str
    title: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RenameShelfSubsectionCommand:
    organization_id: OrganizationId
    section_id: ShelfSectionId
    actor_id: UserId
    expected_version: int
    code: str
    title: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class CreateShelfSlotCommand:
    organization_id: OrganizationId
    actor_id: UserId
    code: str
    title: str
    short_title: str
    document_kind: str
    kept_on: SlotKeptOn
    obligation_level: SlotObligationLevel
    curated_status: CuratedSlotStatus
    applicability_condition: str = ""
    legal_basis: SlotLegalBasis | None = None
    review_cycle_text: str = ""
    review_period_months: int | None = None
    document_type_code: str | None = None
    proposed_document_type: str = ""
    responsible_text: str = ""
    legacy_location: str = ""
    notes: str = ""
    package_code: str = ""
    legacy_code: str = ""
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UpdateShelfSlotCommand:
    """Partial edit; ``changes`` holds only the curated fields the client sent."""

    organization_id: OrganizationId
    slot_id: ShelfSlotId
    actor_id: UserId
    expected_version: int
    changes: Mapping[str, Any] = field(default_factory=dict)
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ExcludeShelfSlotCommand:
    organization_id: OrganizationId
    slot_id: ShelfSlotId
    actor_id: UserId
    expected_version: int
    reason: SlotExclusionReason
    comment: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class BulkExcludeShelfSlotsCommand:
    organization_id: OrganizationId
    actor_id: UserId
    items: tuple[tuple[ShelfSlotId, int], ...]
    """``(slot_id, expected_version)`` pairs; ids are distinct."""
    reason: SlotExclusionReason
    comment: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RestoreShelfSlotCommand:
    organization_id: OrganizationId
    slot_id: ShelfSlotId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ConfirmShelfSlotApplicableCommand:
    organization_id: OrganizationId
    slot_id: ShelfSlotId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class LinkShelfSlotDocumentCommand:
    organization_id: OrganizationId
    slot_id: ShelfSlotId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UnlinkShelfSlotDocumentCommand:
    organization_id: OrganizationId
    slot_id: ShelfSlotId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class DevelopShelfSlotDocumentCommand:
    """Create a draft document from the place and link it in one unit of work."""

    organization_id: OrganizationId
    slot_id: ShelfSlotId
    actor_id: UserId
    expected_version: int
    document_type_code: str | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ImportShelfWorkbookCommand:
    """Workbook import (TASK-P11-012 §3); ``rows`` come from the workbook reader."""

    organization_id: OrganizationId
    actor_id: UserId
    rows: tuple[Any, ...]
    """``WorkbookRow`` items (application/services/shelf_import_mapping.py)."""
    headers: tuple[str, ...]
    file_sha256: str
    dry_run: bool = True
    audit_context: AuditContext | None = None
