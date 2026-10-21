from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.knowledge_objects import PaginationResponse

ComplianceDocumentStatusValue = Literal[
    "draft",
    "approved",
    "active",
    "under_review",
    "superseded",
    "archived",
]
ComplianceDocumentSourceValue = Literal["manual", "generated", "hr_form"]
DocumentSubjectKindValue = Literal["organization", "employee", "asset"]
SafetyDomainValue = Literal[
    "occupational",
    "industrial",
    "labour",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
]


class DocumentApplicabilityPayload(BaseModel):
    """Loose applicability scope; positions/work_types/departments stay free text."""

    model_config = ConfigDict(extra="forbid")

    positions: list[str] = Field(default_factory=list)
    work_types: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    asset_ids: list[UUID] = Field(default_factory=list)


class DocumentFileResponse(BaseModel):
    """Reserved; Phase 4 responses always carry ``null`` here (files land in Phase 5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    bucket: str
    key: str
    size_bytes: int
    content_type: str
    sha256: str
    original_filename: str
    uploaded_at: datetime
    uploaded_by: UUID


class DocumentTypeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    organization_id: UUID
    code: str
    title_ru: str
    safety_domain: SafetyDomainValue
    subject_kind: DocumentSubjectKindValue
    review_period_months: int | None
    validity_months: int | None
    periodicity_months: int | None
    warning_thresholds_days: list[int]
    requires_acknowledgement: bool
    requires_approval_order: bool
    legal_basis: str
    legal_basis_reference: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentTypeListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: list[DocumentTypeResponse]


class ComplianceDocumentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    organization_id: UUID
    document_type_id: UUID
    subject_kind: DocumentSubjectKindValue
    subject_id: UUID | None
    code: str
    title: str
    status: ComplianceDocumentStatusValue
    issued_at: date | None
    effective_from: date | None
    next_review_at: date | None
    approved_by_document_id: UUID | None
    supersedes_document_id: UUID | None
    superseded_by_document_id: UUID | None
    applicability: DocumentApplicabilityPayload
    source: ComplianceDocumentSourceValue
    current_file: DocumentFileResponse | None
    notes: str
    status_before_archive: ComplianceDocumentStatusValue | None
    archive_reason: str | None
    is_review_due: bool
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    version: int


class ComplianceDocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: list[ComplianceDocumentResponse]
    pagination: PaginationResponse


class CreateComplianceDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type_id: UUID
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1)
    subject_id: UUID | None = None
    issued_at: date | None = None
    effective_from: date | None = None
    next_review_at: date | None = None
    approved_by_document_id: UUID | None = None
    supersedes_document_id: UUID | None = None
    applicability: DocumentApplicabilityPayload | None = None
    source: ComplianceDocumentSourceValue = "manual"
    notes: str = ""


class UpdateComplianceDocumentRequest(BaseModel):
    """Partial update of a draft document; omitted fields keep their value.

    ``None`` on an optional date or reference clears it (D14-style explicit
    nullability); omitting the key leaves it untouched.
    """

    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    code: str | None = Field(default=None, min_length=1, max_length=64)
    title: str | None = Field(default=None, min_length=1)
    issued_at: date | None = None
    effective_from: date | None = None
    next_review_at: date | None = None
    approved_by_document_id: UUID | None = None
    supersedes_document_id: UUID | None = None
    applicability: DocumentApplicabilityPayload | None = None
    notes: str | None = None
