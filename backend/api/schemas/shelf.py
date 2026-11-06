"""DTOs of the document shelf API (TASK-P11-012 §2.5, docs/api/ShelfAPI.md)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.api.schemas.compliance_documents import (
    ComplianceDocumentStatusValue,
    SafetyDomainValue,
)
from backend.core.domain.value_objects.shelf_values import normalize_source_url

SlotKeptOnValue = Literal["organization", "facility", "event", "employee", "asset", "profession"]
SlotObligationLevelValue = Literal["mandatory", "conditional", "recommended"]
CuratedSlotStatusValue = Literal[
    "present", "present_needs_review", "in_progress", "missing", "to_clarify"
]
SlotExclusionReasonValue = Literal["not_applicable", "condition_not_met", "duplicate", "other"]
LegalBasisConfidenceValue = Literal["verified", "secondary", "unconfirmed", "none"]
ShelfEffectiveStatusValue = Literal[
    "excluded",
    "present",
    "present_unverified",
    "review_due",
    "overdue_review",
    "under_review",
    "in_progress",
    "missing",
    "to_clarify",
]
ShelfStatusGroupValue = Literal[
    "present", "review", "in_progress", "missing", "to_clarify", "excluded"
]
ShelfActionValue = Literal[
    "develop_document",
    "link_document",
    "exclude",
    "restore",
    "confirm_applicable",
    "open_project",
    "open_document",
    "upload_scan",
    "upload_signed_scan",
    "start_review",
    "send_for_acknowledgement",
]

_RESPONSE = ConfigDict(extra="forbid", frozen=True)
_REQUEST = ConfigDict(extra="forbid")


# ---- responses ----


class ShelfGroupCountsResponse(BaseModel):
    model_config = _RESPONSE

    present: int
    review: int
    in_progress: int
    missing: int
    to_clarify: int
    excluded: int


class ShelfStripItemResponse(BaseModel):
    model_config = _RESPONSE

    code: str
    group: ShelfStatusGroupValue


class ShelfSectionSummaryResponse(BaseModel):
    model_config = _RESPONSE

    code: str
    number: int
    title: str
    safety_domain: SafetyDomainValue
    total: int
    mandatory_total: int
    by_group: ShelfGroupCountsResponse
    readiness_percent: int
    strip: list[ShelfStripItemResponse]


class ShelfTotalsResponse(BaseModel):
    model_config = _RESPONSE

    places: int
    excluded: int
    by_group: ShelfGroupCountsResponse
    readiness_percent: int


class ShelfOverviewResponse(BaseModel):
    model_config = _RESPONSE

    sections: list[ShelfSectionSummaryResponse]
    totals: ShelfTotalsResponse
    evaluated_at: datetime
    last_imported_at: datetime | None
    """Latest workbook import of the organization's places; ``null`` before one."""


class ShelfSlotSummaryResponse(BaseModel):
    model_config = _RESPONSE

    id: UUID
    code: str
    subsection_code: str
    short_title: str
    title: str
    document_kind: str
    kept_on: SlotKeptOnValue
    obligation_level: SlotObligationLevelValue
    effective_status: ShelfEffectiveStatusValue
    group: ShelfStatusGroupValue
    has_acknowledgement_gap: bool
    """Always ``false`` until phase 5 (acknowledgement coverage)."""
    version: int
    """Current place version; bulk commands send it back (optimistic concurrency)."""


class ShelfSlotListResponse(BaseModel):
    model_config = _RESPONSE

    items: list[ShelfSlotSummaryResponse]


class ShelfSectionRefResponse(BaseModel):
    model_config = _RESPONSE

    code: str
    number: int
    title: str


class ShelfSubsectionSlotsResponse(BaseModel):
    model_config = _RESPONSE

    code: str
    title: str
    slots: list[ShelfSlotSummaryResponse]


class ShelfSectionSlotsResponse(BaseModel):
    model_config = _RESPONSE

    section: ShelfSectionRefResponse
    subsections: list[ShelfSubsectionSlotsResponse]


class SlotLegalBasisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regulation: str = ""
    clause: str = ""
    quote: str = ""
    source_url: str | None = None
    confidence: LegalBasisConfidenceValue = "none"

    @field_validator("source_url")
    @classmethod
    def require_http_url(cls, value: str | None) -> str | None:
        return normalize_source_url(value)


class ShelfSlotExclusionResponse(BaseModel):
    model_config = _RESPONSE

    reason: SlotExclusionReasonValue
    comment: str
    excluded_by_name: str
    excluded_at: datetime


class ShelfDocumentRefResponse(BaseModel):
    model_config = _RESPONSE

    code: str
    title: str


class ShelfDocumentFileResponse(BaseModel):
    model_config = _RESPONSE

    file_id: UUID
    content_type: str
    size_bytes: int
    uploaded_at: datetime


class ShelfCurrentDocumentResponse(BaseModel):
    model_config = _RESPONSE

    id: UUID
    code: str
    title: str
    status: ComplianceDocumentStatusValue
    effective_from: date | None
    next_review_at: date | None
    approved_by_order: ShelfDocumentRefResponse | None
    signed_scan: ShelfDocumentFileResponse | None
    """The current signed scan (TASK-P11-012 D1)."""
    working_file: ShelfDocumentFileResponse | None


class ShelfEditionResponse(BaseModel):
    model_config = _RESPONSE

    id: UUID
    code: str
    status: ComplianceDocumentStatusValue
    effective_from: date | None


class ShelfSlotDetailResponse(ShelfSlotSummaryResponse):
    section_code: str
    legal_basis: SlotLegalBasisPayload
    applicability_condition: str
    review_cycle_text: str
    review_period_months: int | None
    review_date: date | None
    curated_status: CuratedSlotStatusValue
    document_type_code: str | None
    proposed_document_type: str
    responsible_text: str
    legacy_location: str
    notes: str
    package_code: str
    legacy_code: str
    exclusion: ShelfSlotExclusionResponse | None
    current_document: ShelfCurrentDocumentResponse | None
    editions: list[ShelfEditionResponse]
    available_actions: list[ShelfActionValue]
    """Every action offered to the current user, ``primary_action`` first."""
    primary_action: ShelfActionValue | None
    acknowledgement: None = None
    """Phase 5; always ``null`` now."""


class DevelopShelfSlotResponse(BaseModel):
    model_config = _RESPONSE

    document_id: UUID
    slot: ShelfSlotDetailResponse


# ---- requests ----


class CreateShelfSlotRequest(BaseModel):
    model_config = _REQUEST

    code: str
    title: str
    short_title: str
    document_kind: str
    kept_on: SlotKeptOnValue
    obligation_level: SlotObligationLevelValue
    curated_status: CuratedSlotStatusValue = "missing"
    applicability_condition: str = ""
    legal_basis: SlotLegalBasisPayload | None = None
    review_cycle_text: str = ""
    review_period_months: int | None = Field(default=None, ge=1)
    document_type_code: str | None = None
    proposed_document_type: str = ""
    responsible_text: str = ""
    legacy_location: str = ""
    notes: str = ""
    package_code: str = ""
    legacy_code: str = ""


class UpdateShelfSlotRequest(BaseModel):
    """Only the fields present in the body change; ``null`` clears nullable ones."""

    model_config = _REQUEST

    version: int = Field(ge=1)
    title: str | None = None
    short_title: str | None = None
    document_kind: str | None = None
    kept_on: SlotKeptOnValue | None = None
    obligation_level: SlotObligationLevelValue | None = None
    curated_status: CuratedSlotStatusValue | None = None
    applicability_condition: str | None = None
    legal_basis: SlotLegalBasisPayload | None = None
    review_cycle_text: str | None = None
    review_period_months: int | None = Field(default=None, ge=1)
    document_type_code: str | None = None
    proposed_document_type: str | None = None
    responsible_text: str | None = None
    legacy_location: str | None = None
    notes: str | None = None
    package_code: str | None = None
    legacy_code: str | None = None


class ShelfSlotVersionRequest(BaseModel):
    model_config = _REQUEST

    version: int = Field(ge=1)


class ExcludeShelfSlotRequest(BaseModel):
    model_config = _REQUEST

    reason: SlotExclusionReasonValue
    comment: str
    version: int = Field(ge=1)


class BulkExcludeItem(BaseModel):
    model_config = _REQUEST

    slot_id: UUID
    version: int = Field(ge=1)


class BulkExcludeShelfSlotsRequest(BaseModel):
    model_config = _REQUEST

    items: list[BulkExcludeItem] = Field(min_length=1, max_length=200)
    reason: SlotExclusionReasonValue
    comment: str


class LinkShelfSlotDocumentRequest(BaseModel):
    model_config = _REQUEST

    document_id: UUID
    version: int = Field(ge=1)


class DevelopShelfSlotRequest(BaseModel):
    model_config = _REQUEST

    document_type_code: str | None = None
    version: int = Field(ge=1)
