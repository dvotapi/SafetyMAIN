from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.exceptions.shelf import (
    ShelfSlotAlreadyExcluded,
    ShelfSlotCodeMismatch,
    ShelfSlotDocumentAlreadyLinked,
    ShelfSlotDocumentNotFound,
    ShelfSlotDocumentNotLinked,
    ShelfSlotDocumentSubjectNotSupported,
    ShelfSlotExclusionCommentTooShort,
    ShelfSlotNotExcluded,
    ShelfSlotNotToClarify,
    ShelfSlotValidationError,
    ShelfSlotVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
    ShelfSubsectionId,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_slot_code import ShelfSlotCode
from backend.core.domain.value_objects.shelf_values import (
    EXCLUSION_COMMENT_MIN_LENGTH,
    SHELF_DOCUMENT_KINDS,
    SlotExclusion,
    SlotLegalBasis,
)

SHORT_TITLE_MAX_LENGTH = 40
TITLE_MAX_LENGTH = 500

_IN_FORCE = frozenset(
    {ComplianceDocumentStatus.ACTIVE, ComplianceDocumentStatus.UNDER_REVIEW}
)
# A place holding a document in one of these statuses has no room for a new draft.
_HOLDING = _IN_FORCE | {ComplianceDocumentStatus.DRAFT, ComplianceDocumentStatus.APPROVED}

# Curated fields `update_details` may change (never code, section, exclusion, links).
_EDITABLE_FIELDS = frozenset(
    {
        "title",
        "short_title",
        "document_kind",
        "kept_on",
        "obligation_level",
        "applicability_condition",
        "legal_basis",
        "review_cycle_text",
        "review_period_months",
        "curated_status",
        "document_type_code",
        "proposed_document_type",
        "responsible_text",
        "legacy_location",
        "notes",
        "package_code",
        "legacy_code",
    }
)


class ShelfSlot(BaseModel):
    """A place on the document shelf (TASK-P11-012 D2).

    A place exists whether or not its document does; it is never deleted.
    Excluded places stay on the shelf and can be restored (D11).
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: ShelfSlotId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    code: ShelfSlotCode = Field(frozen=True)
    section_id: ShelfSectionId = Field(frozen=True)
    subsection_id: ShelfSubsectionId = Field(frozen=True)
    title: str
    short_title: str
    document_kind: str
    kept_on: SlotKeptOn
    obligation_level: SlotObligationLevel
    applicability_condition: str = ""
    legal_basis: SlotLegalBasis = Field(default_factory=SlotLegalBasis)
    review_cycle_text: str = ""
    review_period_months: int | None = None
    curated_status: CuratedSlotStatus
    document_type_code: str | None = None
    proposed_document_type: str = ""
    responsible_text: str = ""
    legacy_location: str = ""
    notes: str = ""
    package_code: str = ""
    legacy_code: str = ""
    exclusion: SlotExclusion | None = None
    linked_document_ids: tuple[ComplianceDocumentId, ...] = ()
    import_fingerprint: str | None = None
    last_imported_at: datetime | None = None
    created_at: datetime = Field(frozen=True)
    created_by: UserId
    updated_at: datetime
    updated_by: UserId
    version: int = 1

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Shelf place title is required.")
        if len(normalized) > TITLE_MAX_LENGTH:
            raise ValueError(
                f"Shelf place title must be at most {TITLE_MAX_LENGTH} characters."
            )
        return normalized

    @field_validator("short_title")
    @classmethod
    def require_short_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Shelf place short title is required.")
        if len(normalized) > SHORT_TITLE_MAX_LENGTH:
            raise ValueError(
                "Shelf place short title must be at most "
                f"{SHORT_TITLE_MAX_LENGTH} characters."
            )
        return normalized

    @field_validator("document_kind")
    @classmethod
    def require_known_kind(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in SHELF_DOCUMENT_KINDS:
            raise ValueError(f"Unknown document kind: {normalized}.")
        return normalized

    @field_validator(
        "applicability_condition",
        "review_cycle_text",
        "proposed_document_type",
        "responsible_text",
        "legacy_location",
        "notes",
        "package_code",
        "legacy_code",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("document_type_code")
    @classmethod
    def normalize_type_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("review_period_months")
    @classmethod
    def require_positive_period(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("Shelf place review period must be positive.")
        return value

    @field_validator("version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Shelf place version must be positive.")
        return value

    @model_validator(mode="after")
    def check_invariants(self) -> ShelfSlot:
        if (
            self.obligation_level is SlotObligationLevel.CONDITIONAL
            and not self.applicability_condition
        ):
            raise ValueError("A conditional place requires an applicability condition.")
        if len(set(self.linked_document_ids)) != len(self.linked_document_ids):
            raise ValueError("A document is linked to a place at most once.")
        return self

    @property
    def is_excluded(self) -> bool:
        return self.exclusion is not None

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        section: ShelfSection,
        code: str,
        title: str,
        short_title: str,
        document_kind: str,
        kept_on: SlotKeptOn,
        obligation_level: SlotObligationLevel,
        curated_status: CuratedSlotStatus,
        created_by: UserId,
        created_at: datetime,
        applicability_condition: str = "",
        legal_basis: SlotLegalBasis | None = None,
        review_cycle_text: str = "",
        review_period_months: int | None = None,
        document_type_code: str | None = None,
        proposed_document_type: str = "",
        responsible_text: str = "",
        legacy_location: str = "",
        notes: str = "",
        package_code: str = "",
        legacy_code: str = "",
        slot_id: ShelfSlotId | None = None,
        import_fingerprint: str | None = None,
    ) -> ShelfSlot:
        """``import_fingerprint`` is set only by the workbook import (it also
        sets ``last_imported_at`` = ``created_at``)."""
        try:
            slot_code = ShelfSlotCode(value=code)
        except ValidationError as error:
            raise ShelfSlotValidationError(_message(error)) from error
        subsection = section.subsection(slot_code.subsection_code)
        if (
            section.organization_id != organization_id
            or slot_code.section_code != section.code
            or subsection is None
        ):
            raise ShelfSlotCodeMismatch(code=code, section_code=section.code)
        return _validated(
            id=slot_id or ShelfSlotId(value=uuid4()),
            organization_id=organization_id,
            code=slot_code,
            section_id=section.id,
            subsection_id=subsection.id,
            title=title,
            short_title=short_title,
            document_kind=document_kind,
            kept_on=kept_on,
            obligation_level=obligation_level,
            applicability_condition=applicability_condition,
            legal_basis=legal_basis or SlotLegalBasis(),
            review_cycle_text=review_cycle_text,
            review_period_months=review_period_months,
            curated_status=curated_status,
            document_type_code=document_type_code,
            proposed_document_type=proposed_document_type,
            responsible_text=responsible_text,
            legacy_location=legacy_location,
            notes=notes,
            package_code=package_code,
            legacy_code=legacy_code,
            import_fingerprint=import_fingerprint,
            last_imported_at=created_at if import_fingerprint is not None else None,
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
        **changes: Any,
    ) -> ShelfSlot:
        """Edit curated fields. Returns ``self`` when nothing changes.

        The curated status of an excluded place is frozen until it is restored.
        """
        self._assert_version(expected_version)
        unknown = set(changes) - _EDITABLE_FIELDS
        if unknown:
            raise ShelfSlotValidationError(
                "Fields cannot be edited: " + ", ".join(sorted(unknown)) + "."
            )
        candidate = _validated(**{**dict(self), **changes})
        if candidate == self:
            return self
        if self.is_excluded and candidate.curated_status is not self.curated_status:
            raise ShelfSlotAlreadyExcluded(self.id)
        return self._mutated(at=at, actor_id=actor_id, **changes)

    def apply_import(
        self,
        *,
        values: dict[str, Any],
        fingerprint: str,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ShelfSlot:
        """Workbook import (D3): set mapped curated fields and the import marks.

        Always a new version, because the fingerprint changes. Exclusion and links
        are untouched; on an excluded place the curated status stays frozen.
        """
        self._assert_version(expected_version)
        unknown = set(values) - _EDITABLE_FIELDS
        if unknown:
            raise ShelfSlotValidationError(
                "Fields cannot be imported: " + ", ".join(sorted(unknown)) + "."
            )
        if (
            self.is_excluded
            and "curated_status" in values
            and values["curated_status"] is not self.curated_status
        ):
            raise ShelfSlotAlreadyExcluded(self.id)
        return self._mutated(
            at=at,
            actor_id=actor_id,
            **values,
            import_fingerprint=fingerprint,
            last_imported_at=at,
        )

    def exclude(
        self,
        *,
        reason: SlotExclusionReason,
        comment: str,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ShelfSlot:
        self._assert_version(expected_version)
        self._assert_not_excluded()
        if len(comment.strip()) < EXCLUSION_COMMENT_MIN_LENGTH:
            raise ShelfSlotExclusionCommentTooShort(min_length=EXCLUSION_COMMENT_MIN_LENGTH)
        try:
            exclusion = SlotExclusion(
                reason=reason,
                comment=comment,
                status_before=self.curated_status,
                excluded_by=actor_id,
                excluded_at=at,
            )
        except ValidationError as error:
            raise ShelfSlotValidationError(_message(error)) from error
        return self._mutated(at=at, actor_id=actor_id, exclusion=exclusion)

    def restore(
        self, *, at: datetime, actor_id: UserId, expected_version: int
    ) -> ShelfSlot:
        self._assert_version(expected_version)
        if self.exclusion is None:
            raise ShelfSlotNotExcluded(self.id)
        return self._mutated(
            at=at,
            actor_id=actor_id,
            exclusion=None,
            curated_status=self.exclusion.status_before,
        )

    def confirm_applicable(
        self, *, at: datetime, actor_id: UserId, expected_version: int
    ) -> ShelfSlot:
        """«Требуется»: a place to clarify becomes a missing one."""
        self._assert_version(expected_version)
        self._assert_not_excluded()
        if self.curated_status is not CuratedSlotStatus.TO_CLARIFY:
            raise ShelfSlotNotToClarify(self.id, curated_status=self.curated_status.value)
        return self._mutated(
            at=at, actor_id=actor_id, curated_status=CuratedSlotStatus.MISSING
        )

    def ensure_can_develop(self, linked_documents: Iterable[ComplianceDocument]) -> None:
        """A new draft is allowed only when no linked document is in progress or in force."""
        self._assert_not_excluded()
        holding = self._linked(linked_documents, _HOLDING)
        if holding:
            raise ShelfSlotDocumentAlreadyLinked(slot_id=self.id, document_id=holding[0].id)

    def link_document(
        self,
        *,
        document: ComplianceDocument,
        linked_documents: Iterable[ComplianceDocument],
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ShelfSlot:
        """Link a document of the same organization. Returns ``self`` if already linked.

        ``linked_documents`` are the currently linked documents (others are ignored);
        at most one linked document is in force.
        """
        self._assert_version(expected_version)
        self._assert_not_excluded()
        if document.organization_id != self.organization_id:
            raise ShelfSlotDocumentNotFound(document.id)
        if document.subject_kind is not DocumentSubjectKind.ORGANIZATION:
            raise ShelfSlotDocumentSubjectNotSupported(
                document_id=document.id, subject_kind=document.subject_kind.value
            )
        if document.id in self.linked_document_ids:
            return self
        if document.status in _IN_FORCE:
            in_force = self._linked(linked_documents, _IN_FORCE)
            if in_force:
                raise ShelfSlotDocumentAlreadyLinked(
                    slot_id=self.id, document_id=in_force[0].id
                )
        return self._mutated(
            at=at,
            actor_id=actor_id,
            linked_document_ids=(*self.linked_document_ids, document.id),
        )

    def unlink_document(
        self,
        *,
        document_id: ComplianceDocumentId,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> ShelfSlot:
        self._assert_version(expected_version)
        self._assert_not_excluded()
        if document_id not in self.linked_document_ids:
            raise ShelfSlotDocumentNotLinked(slot_id=self.id, document_id=document_id)
        return self._mutated(
            at=at,
            actor_id=actor_id,
            linked_document_ids=tuple(
                item for item in self.linked_document_ids if item != document_id
            ),
        )

    def _linked(
        self,
        documents: Iterable[ComplianceDocument],
        statuses: frozenset[ComplianceDocumentStatus],
    ) -> list[ComplianceDocument]:
        return [
            document
            for document in documents
            if document.id in self.linked_document_ids and document.status in statuses
        ]

    def _mutated(self, *, at: datetime, actor_id: UserId, **updates: Any) -> ShelfSlot:
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
            raise ShelfSlotVersionConflict(
                slot_id=self.id,
                expected_version=expected_version,
                actual_version=self.version,
            )

    def _assert_not_excluded(self) -> None:
        if self.exclusion is not None:
            raise ShelfSlotAlreadyExcluded(self.id)


def _message(error: ValidationError) -> str:
    detail = error.errors()[0]
    return str(detail.get("ctx", {}).get("error") or detail["msg"])


def _validated(**fields: Any) -> ShelfSlot:
    try:
        return ShelfSlot(**fields)
    except ValidationError as error:
        raise ShelfSlotValidationError(_message(error)) from error
