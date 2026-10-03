from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.core.domain.services.calendar_months import add_months
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.domain.value_objects.safety_ids import DocumentTypeId

DEFAULT_WARNING_THRESHOLDS_DAYS: tuple[int, ...] = (90, 30, 14, 7)


class DocumentType(BaseModel):
    """Organization-scoped catalog entry describing a kind of compliance document.

    A type carries at most one period: ``review_period_months`` (planned review
    of local acts), ``validity_months`` (employee permits), or
    ``periodicity_months`` (recurring briefings).
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: DocumentTypeId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    code: str
    title_ru: str
    safety_domain: SafetyDomain
    subject_kind: DocumentSubjectKind
    review_period_months: int | None = None
    validity_months: int | None = None
    periodicity_months: int | None = None
    warning_thresholds_days: tuple[int, ...] = DEFAULT_WARNING_THRESHOLDS_DAYS
    requires_acknowledgement: bool = False
    requires_approval_order: bool = False
    legal_basis: str = ""
    legal_basis_reference: str | None = None
    is_active: bool = True
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Document type code must not be empty.")
        if len(normalized) > 64:
            raise ValueError("Document type code must be at most 64 characters.")
        return normalized

    @field_validator("title_ru")
    @classmethod
    def require_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Document type title is required.")
        return normalized

    @field_validator("review_period_months", "validity_months", "periodicity_months")
    @classmethod
    def require_positive_period(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("Document type periods must be positive.")
        return value

    @field_validator("warning_thresholds_days")
    @classmethod
    def require_positive_thresholds(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value:
            raise ValueError("At least one warning threshold is required.")
        if any(days < 1 for days in value):
            raise ValueError("Warning thresholds must be positive.")
        return value

    @field_validator("legal_basis")
    @classmethod
    def normalize_legal_basis(cls, value: str) -> str:
        return value.strip()

    @field_validator("legal_basis_reference")
    @classmethod
    def normalize_legal_basis_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def require_single_period_kind(self) -> DocumentType:
        periods = (
            self.review_period_months,
            self.validity_months,
            self.periodicity_months,
        )
        if sum(period is not None for period in periods) > 1:
            raise ValueError(
                "A document type has at most one of review, validity, or periodicity."
            )
        return self

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        code: str,
        title_ru: str,
        safety_domain: SafetyDomain,
        subject_kind: DocumentSubjectKind,
        created_at: datetime,
        review_period_months: int | None = None,
        validity_months: int | None = None,
        periodicity_months: int | None = None,
        warning_thresholds_days: tuple[int, ...] = DEFAULT_WARNING_THRESHOLDS_DAYS,
        requires_acknowledgement: bool = False,
        requires_approval_order: bool = False,
        legal_basis: str = "",
        legal_basis_reference: str | None = None,
        is_active: bool = True,
        document_type_id: DocumentTypeId | None = None,
    ) -> DocumentType:
        return cls(
            id=document_type_id or DocumentTypeId(value=uuid4()),
            organization_id=organization_id,
            code=code,
            title_ru=title_ru,
            safety_domain=safety_domain,
            subject_kind=subject_kind,
            review_period_months=review_period_months,
            validity_months=validity_months,
            periodicity_months=periodicity_months,
            warning_thresholds_days=warning_thresholds_days,
            requires_acknowledgement=requires_acknowledgement,
            requires_approval_order=requires_approval_order,
            legal_basis=legal_basis,
            legal_basis_reference=legal_basis_reference,
            is_active=is_active,
            created_at=created_at,
            updated_at=created_at,
        )

    def next_review_from(self, start: date) -> date | None:
        """Planned review date counted from ``start``; ``None`` without a review period."""
        if self.review_period_months is None:
            return None
        return add_months(start, self.review_period_months)

    def review_due_cutoff(self, as_of: date) -> date | None:
        """Latest ``next_review_at`` that counts as review-due on ``as_of`` (D11)."""
        if self.review_period_months is None:
            return None
        return as_of + timedelta(days=max(self.warning_thresholds_days))
