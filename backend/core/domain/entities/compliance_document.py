from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentCannotBeModified,
    ComplianceDocumentReasonRequired,
    ComplianceDocumentValidationError,
    ComplianceDocumentVersionConflict,
    InvalidComplianceDocumentTransition,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentApplicability,
    DocumentFile,
)
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentSource,
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
)

_IN_FORCE = frozenset(
    {ComplianceDocumentStatus.ACTIVE, ComplianceDocumentStatus.UNDER_REVIEW}
)

# Restore is not a graph edge: it returns an archived document to the status it
# held before archiving (D8).
_TRANSITIONS: dict[str, frozenset[str]] = {
    ComplianceDocumentStatus.DRAFT.value: frozenset(
        {
            ComplianceDocumentStatus.APPROVED.value,
            ComplianceDocumentStatus.ARCHIVED.value,
        }
    ),
    ComplianceDocumentStatus.APPROVED.value: frozenset(
        {
            ComplianceDocumentStatus.ACTIVE.value,
            ComplianceDocumentStatus.ARCHIVED.value,
        }
    ),
    ComplianceDocumentStatus.ACTIVE.value: frozenset(
        {
            ComplianceDocumentStatus.UNDER_REVIEW.value,
            ComplianceDocumentStatus.SUPERSEDED.value,
            ComplianceDocumentStatus.ARCHIVED.value,
        }
    ),
    ComplianceDocumentStatus.UNDER_REVIEW.value: frozenset(
        {
            ComplianceDocumentStatus.ACTIVE.value,
            ComplianceDocumentStatus.SUPERSEDED.value,
        }
    ),
    ComplianceDocumentStatus.SUPERSEDED.value: frozenset(
        {ComplianceDocumentStatus.ARCHIVED.value}
    ),
    ComplianceDocumentStatus.ARCHIVED.value: frozenset(),
}


class ComplianceDocument(BaseModel):
    """Organization-scoped compliance document aggregate root (P11-001).

    Files attach only in ``draft`` (D6); changing an active document means a new
    edition that supersedes it.
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: ComplianceDocumentId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    document_type_id: DocumentTypeId
    subject_kind: DocumentSubjectKind = Field(frozen=True)
    subject_id: UUID | None = Field(default=None, frozen=True)
    code: str
    title: str
    status: ComplianceDocumentStatus = ComplianceDocumentStatus.DRAFT
    issued_at: date | None = None
    effective_from: date | None = None
    next_review_at: date | None = None
    approved_by_document_id: ComplianceDocumentId | None = None
    supersedes_document_id: ComplianceDocumentId | None = None
    superseded_by_document_id: ComplianceDocumentId | None = None
    applicability: DocumentApplicability = Field(default_factory=DocumentApplicability)
    source: ComplianceDocumentSource = ComplianceDocumentSource.MANUAL
    files: tuple[DocumentFile, ...] = ()
    notes: str = ""
    status_before_archive: ComplianceDocumentStatus | None = None
    archive_reason: str | None = None
    created_at: datetime = Field(frozen=True)
    created_by: UserId
    updated_at: datetime
    updated_by: UserId
    version: int = 1

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Compliance document code is required.")
        if len(normalized) > 64:
            raise ValueError("Compliance document code must be at most 64 characters.")
        return normalized

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Compliance document title is required.")
        return normalized

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str) -> str:
        return value.strip()

    @field_validator("version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Compliance document version must be positive.")
        return value

    @model_validator(mode="after")
    def check_subject_and_references(self) -> ComplianceDocument:
        if self.subject_kind is DocumentSubjectKind.ORGANIZATION:
            if self.subject_id is not None:
                raise ValueError("Organization documents have no subject id.")
        elif self.subject_id is None:
            raise ValueError(f"A {self.subject_kind.value} document requires a subject id.")
        references = (
            self.approved_by_document_id,
            self.supersedes_document_id,
            self.superseded_by_document_id,
        )
        if self.id in references:
            raise ValueError("A compliance document cannot reference itself.")
        return self

    @property
    def current_file(self) -> DocumentFile | None:
        return self.files[-1] if self.files else None

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        document_type: DocumentType,
        code: str,
        title: str,
        created_by: UserId,
        created_at: datetime,
        subject_id: UUID | None = None,
        issued_at: date | None = None,
        effective_from: date | None = None,
        next_review_at: date | None = None,
        approved_by_document_id: ComplianceDocumentId | None = None,
        supersedes_document_id: ComplianceDocumentId | None = None,
        applicability: DocumentApplicability | None = None,
        source: ComplianceDocumentSource = ComplianceDocumentSource.MANUAL,
        notes: str = "",
        document_id: ComplianceDocumentId | None = None,
    ) -> ComplianceDocument:
        _assert_usable_type(document_type, organization_id=organization_id)
        return _validated(
            id=document_id or ComplianceDocumentId(value=uuid4()),
            organization_id=organization_id,
            document_type_id=document_type.id,
            subject_kind=document_type.subject_kind,
            subject_id=subject_id,
            code=code,
            title=title,
            issued_at=issued_at,
            effective_from=effective_from,
            next_review_at=next_review_at,
            approved_by_document_id=approved_by_document_id,
            supersedes_document_id=supersedes_document_id,
            applicability=applicability or DocumentApplicability(),
            source=source,
            notes=notes,
            created_at=created_at,
            created_by=created_by,
            updated_at=created_at,
            updated_by=created_by,
            version=1,
        )

    def update_details(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        document_type: DocumentType | None = None,
        code: str | None = None,
        title: str | None = None,
        issued_at: date | None | object = ...,
        effective_from: date | None | object = ...,
        next_review_at: date | None | object = ...,
        approved_by_document_id: ComplianceDocumentId | None | object = ...,
        supersedes_document_id: ComplianceDocumentId | None | object = ...,
        applicability: DocumentApplicability | None = None,
        notes: str | None = None,
    ) -> ComplianceDocument:
        """Edit a draft. ``None`` clears a nullable field; an omitted one is kept."""
        self._assert_version(expected_version)
        self._assert_draft("detail edits")
        updates: dict[str, Any] = {}
        if document_type is not None:
            _assert_usable_type(
                document_type,
                organization_id=self.organization_id,
                subject_kind=self.subject_kind,
            )
            updates["document_type_id"] = document_type.id
        if code is not None:
            updates["code"] = code
        if title is not None:
            updates["title"] = title
        if applicability is not None:
            updates["applicability"] = applicability
        if notes is not None:
            updates["notes"] = notes
        nullable = {
            "issued_at": issued_at,
            "effective_from": effective_from,
            "next_review_at": next_review_at,
            "approved_by_document_id": approved_by_document_id,
            "supersedes_document_id": supersedes_document_id,
        }
        updates.update(
            {name: value for name, value in nullable.items() if value is not ...}
        )
        return self._mutated(at=at, actor_id=actor_id, **updates)

    def attach_file(
        self,
        *,
        file: DocumentFile,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ComplianceDocument:
        self._assert_version(expected_version)
        self._assert_draft("file attachment")
        if any(existing.key == file.key for existing in self.files):
            raise ComplianceDocumentValidationError("The file is already attached.")
        return self._mutated(at=at, actor_id=actor_id, files=(*self.files, file))

    def approve(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ComplianceDocument:
        self._assert_version(expected_version)
        self._assert_transition(ComplianceDocumentStatus.APPROVED)
        if self.current_file is None:
            raise ComplianceDocumentValidationError("A file is required before approval.")
        return self._mutated(
            at=at, actor_id=actor_id, status=ComplianceDocumentStatus.APPROVED
        )

    def activate(
        self,
        *,
        document_type: DocumentType,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ComplianceDocument:
        """Activate an approved document.

        Superseding the previous edition is a separate ``supersede`` call on that
        edition within the same unit of work.
        """
        self._assert_version(expected_version)
        self._assert_status(
            ComplianceDocumentStatus.APPROVED, target=ComplianceDocumentStatus.ACTIVE
        )
        self._assert_own_type(document_type)
        if self.current_file is None:
            raise ComplianceDocumentValidationError("A file is required before activation.")
        if self.effective_from is None:
            raise ComplianceDocumentValidationError(
                "An effective-from date is required before activation."
            )
        if document_type.requires_approval_order and self.approved_by_document_id is None:
            raise ComplianceDocumentValidationError(
                "An approval order is required before activation."
            )
        next_review_at = self.next_review_at
        if next_review_at is None:
            next_review_at = document_type.next_review_from(self.effective_from)
        return self._mutated(
            at=at,
            actor_id=actor_id,
            status=ComplianceDocumentStatus.ACTIVE,
            next_review_at=next_review_at,
        )

    def start_review(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ComplianceDocument:
        self._assert_version(expected_version)
        self._assert_transition(ComplianceDocumentStatus.UNDER_REVIEW)
        return self._mutated(
            at=at, actor_id=actor_id, status=ComplianceDocumentStatus.UNDER_REVIEW
        )

    def complete_review(
        self,
        *,
        document_type: DocumentType,
        completed_on: date,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        next_review_at: date | None = None,
    ) -> ComplianceDocument:
        """Return to ``active`` with the next review counted from ``completed_on`` (D7)."""
        self._assert_version(expected_version)
        self._assert_status(
            ComplianceDocumentStatus.UNDER_REVIEW,
            target=ComplianceDocumentStatus.ACTIVE,
        )
        self._assert_own_type(document_type)
        if next_review_at is None:
            next_review_at = document_type.next_review_from(completed_on)
        return self._mutated(
            at=at,
            actor_id=actor_id,
            status=ComplianceDocumentStatus.ACTIVE,
            next_review_at=next_review_at,
        )

    def supersede(
        self,
        *,
        replacement: ComplianceDocument,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ComplianceDocument:
        self._assert_version(expected_version)
        self._assert_transition(ComplianceDocumentStatus.SUPERSEDED)
        if replacement.organization_id != self.organization_id:
            raise ComplianceDocumentValidationError(
                "The replacement belongs to another organization."
            )
        if replacement.supersedes_document_id != self.id:
            raise ComplianceDocumentValidationError(
                "The replacement does not supersede this document."
            )
        if replacement.document_type_id != self.document_type_id:
            raise ComplianceDocumentValidationError(
                "The replacement must have the same document type."
            )
        if replacement.status is not ComplianceDocumentStatus.ACTIVE:
            raise ComplianceDocumentValidationError("The replacement must be active.")
        return self._mutated(
            at=at,
            actor_id=actor_id,
            status=ComplianceDocumentStatus.SUPERSEDED,
            superseded_by_document_id=replacement.id,
        )

    def archive(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        reason: str,
    ) -> ComplianceDocument:
        self._assert_version(expected_version)
        if not reason.strip():
            raise ComplianceDocumentReasonRequired("Archive")
        self._assert_transition(ComplianceDocumentStatus.ARCHIVED)
        return self._mutated(
            at=at,
            actor_id=actor_id,
            status=ComplianceDocumentStatus.ARCHIVED,
            status_before_archive=self.status,
            archive_reason=reason.strip(),
        )

    def restore(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        reason: str,
    ) -> ComplianceDocument:
        self._assert_version(expected_version)
        if not reason.strip():
            raise ComplianceDocumentReasonRequired("Restore")
        if self.status is not ComplianceDocumentStatus.ARCHIVED:
            raise InvalidComplianceDocumentTransition(
                document_id=self.id,
                source=self.status.value,
                target="restore",
            )
        return self._mutated(
            at=at,
            actor_id=actor_id,
            status=self.status_before_archive or ComplianceDocumentStatus.DRAFT,
            status_before_archive=None,
            archive_reason=None,
        )

    def is_review_due(self, *, as_of: date, document_type: DocumentType) -> bool:
        """Backend-computed review-due flag (D11).

        ``next_review_at <= as_of + max(warning_thresholds_days)`` for documents
        in force (``active`` or ``under_review``); always ``False`` when the type
        has no review period or ``next_review_at`` is not set.
        """
        self._assert_own_type(document_type)
        if self.status not in _IN_FORCE or self.next_review_at is None:
            return False
        cutoff = document_type.review_due_cutoff(as_of)
        if cutoff is None:
            return False
        return self.next_review_at <= cutoff

    def _mutated(
        self, *, at: datetime, actor_id: UserId, **updates: Any
    ) -> ComplianceDocument:
        return _validated(
            **{
                **dict(self),
                **updates,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def _assert_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise ComplianceDocumentVersionConflict(
                document_id=self.id,
                expected_version=expected_version,
                actual_version=self.version,
            )

    def _assert_draft(self, action: str) -> None:
        if self.status is not ComplianceDocumentStatus.DRAFT:
            raise ComplianceDocumentCannotBeModified(
                self.id,
                reason=f"status {self.status.value} blocks {action}",
            )

    def _assert_status(
        self,
        source: ComplianceDocumentStatus,
        *,
        target: ComplianceDocumentStatus,
    ) -> None:
        if self.status is not source:
            raise InvalidComplianceDocumentTransition(
                document_id=self.id,
                source=self.status.value,
                target=target.value,
            )

    def _assert_transition(self, target: ComplianceDocumentStatus) -> None:
        permitted = _TRANSITIONS.get(self.status.value, frozenset())
        if target.value not in permitted:
            raise InvalidComplianceDocumentTransition(
                document_id=self.id,
                source=self.status.value,
                target=target.value,
            )

    def _assert_own_type(self, document_type: DocumentType) -> None:
        if (
            document_type.id != self.document_type_id
            or document_type.organization_id != self.organization_id
        ):
            raise ComplianceDocumentValidationError(
                "The document type does not match the document."
            )


def is_in_force(status: ComplianceDocumentStatus) -> bool:
    """``active`` and ``under_review`` documents are in force and own their code (D9)."""
    return status in _IN_FORCE


def _assert_usable_type(
    document_type: DocumentType,
    *,
    organization_id: OrganizationId,
    subject_kind: DocumentSubjectKind | None = None,
) -> None:
    if document_type.organization_id != organization_id:
        raise ComplianceDocumentValidationError(
            "The document type belongs to another organization."
        )
    if not document_type.is_active:
        raise ComplianceDocumentValidationError("The document type is inactive.")
    if subject_kind is not None and document_type.subject_kind is not subject_kind:
        raise ComplianceDocumentValidationError(
            "The document type has a different subject kind."
        )


def _validated(**fields: Any) -> ComplianceDocument:
    try:
        return ComplianceDocument(**fields)
    except ValidationError as error:
        detail = error.errors()[0]
        message = detail.get("ctx", {}).get("error") or detail["msg"]
        raise ComplianceDocumentValidationError(str(message)) from error
