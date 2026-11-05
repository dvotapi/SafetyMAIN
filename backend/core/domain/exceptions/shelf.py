from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
)


class ShelfError(SafetyMainDomainError):
    """Base error for the document shelf (TASK-P11-012)."""


class ShelfSectionNotFound(ShelfError):
    def __init__(self, reference: ShelfSectionId | str) -> None:
        self.reference = reference
        shown = reference.value if isinstance(reference, ShelfSectionId) else reference
        super().__init__(f"Shelf section was not found: {shown}.")


class DuplicateShelfSectionCode(ShelfError):
    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(f"Shelf section code already exists in organization: {code}.")


class DuplicateShelfSectionNumber(ShelfError):
    def __init__(self, *, organization_id: object, number: int) -> None:
        self.organization_id = organization_id
        self.number = number
        super().__init__(
            f"Shelf section number already exists in organization: {number}."
        )


class ShelfSectionValidationError(ShelfError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ShelfSectionVersionConflict(ShelfError):
    def __init__(
        self, *, section_id: ShelfSectionId, expected_version: int, actual_version: int
    ) -> None:
        self.section_id = section_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Shelf section version conflict: "
            f"expected {expected_version}, actual {actual_version}."
        )


class ShelfSlotNotFound(ShelfError):
    def __init__(self, slot_id: ShelfSlotId) -> None:
        self.slot_id = slot_id
        super().__init__(f"Shelf place was not found: {slot_id.value}.")


class DuplicateShelfSlotCode(ShelfError):
    """Codes are unique per organization, excluded places included."""

    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(f"Shelf place code already exists in organization: {code}.")


class ShelfSlotCodeMismatch(ShelfError):
    """The code does not belong to the given section or names no subsection."""

    def __init__(self, *, code: str, section_code: str) -> None:
        self.code = code
        self.section_code = section_code
        super().__init__(
            f"Shelf place code {code} does not match a subsection of section {section_code}."
        )


class ShelfSlotValidationError(ShelfError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ShelfSlotVersionConflict(ShelfError):
    def __init__(
        self, *, slot_id: ShelfSlotId, expected_version: int, actual_version: int
    ) -> None:
        self.slot_id = slot_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Shelf place version conflict: "
            f"expected {expected_version}, actual {actual_version}."
        )


class ShelfSlotAlreadyExcluded(ShelfError):
    def __init__(self, slot_id: ShelfSlotId) -> None:
        self.slot_id = slot_id
        super().__init__(f"Shelf place is excluded: {slot_id.value}.")


class ShelfSlotNotExcluded(ShelfError):
    def __init__(self, slot_id: ShelfSlotId) -> None:
        self.slot_id = slot_id
        super().__init__(f"Shelf place is not excluded: {slot_id.value}.")


class ShelfSlotNotToClarify(ShelfError):
    def __init__(self, slot_id: ShelfSlotId, *, curated_status: str) -> None:
        self.slot_id = slot_id
        self.curated_status = curated_status
        super().__init__(
            f"Only a place to clarify can be confirmed applicable; status is {curated_status}."
        )


class ShelfSlotExclusionCommentTooShort(ShelfError):
    def __init__(self, *, min_length: int) -> None:
        self.min_length = min_length
        super().__init__(
            f"Exclusion comment must have at least {min_length} characters."
        )


class ShelfSlotDocumentSubjectNotSupported(ShelfError):
    """Only organization documents can be kept on a place (employee/asset: P11-008)."""

    def __init__(self, *, document_id: ComplianceDocumentId, subject_kind: str) -> None:
        self.document_id = document_id
        self.subject_kind = subject_kind
        super().__init__(
            f"A {subject_kind} document cannot be linked to a shelf place."
        )


class ShelfSlotDocumentAlreadyLinked(ShelfError):
    """The place already holds a document in force or in progress."""

    def __init__(self, *, slot_id: ShelfSlotId, document_id: ComplianceDocumentId) -> None:
        self.slot_id = slot_id
        self.document_id = document_id
        super().__init__(
            f"Shelf place {slot_id.value} already holds document {document_id.value}."
        )


class ShelfSlotDocumentNotLinked(ShelfError):
    def __init__(self, *, slot_id: ShelfSlotId, document_id: ComplianceDocumentId) -> None:
        self.slot_id = slot_id
        self.document_id = document_id
        super().__init__(
            f"Document {document_id.value} is not linked to shelf place {slot_id.value}."
        )


class ShelfSlotDocumentNotFound(ShelfError):
    """The document does not exist in the place's organization (presents as 404)."""

    def __init__(self, document_id: ComplianceDocumentId) -> None:
        self.document_id = document_id
        super().__init__(f"Compliance document was not found: {document_id.value}.")


class ShelfSlotDocumentTypeRequired(ShelfError):
    """Developing a document needs a type from the request or the place."""

    def __init__(self, slot_id: ShelfSlotId) -> None:
        self.slot_id = slot_id
        super().__init__(f"Shelf place {slot_id.value} has no document type to develop.")


class ShelfSlotDocumentTypeUnknown(ShelfError):
    """A place names a document type code that is missing or inactive in the catalog."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Document type is not in the active catalog: {code}.")


class ShelfSlotsVersionConflict(ShelfError):
    """Bulk command: one or more places changed since the client read them."""

    def __init__(self, slot_ids: tuple[ShelfSlotId, ...]) -> None:
        self.slot_ids = slot_ids
        super().__init__(f"{len(slot_ids)} shelf place(s) have a version conflict.")

    def public_details(self) -> dict[str, object]:
        return {"conflicting_slot_ids": [str(slot_id.value) for slot_id in self.slot_ids]}


class ShelfSlotsAlreadyExcluded(ShelfError):
    """Bulk command: one or more places are already excluded."""

    def __init__(self, slot_ids: tuple[ShelfSlotId, ...]) -> None:
        self.slot_ids = slot_ids
        super().__init__(f"{len(slot_ids)} shelf place(s) are already excluded.")

    def public_details(self) -> dict[str, object]:
        return {"excluded_slot_ids": [str(slot_id.value) for slot_id in self.slot_ids]}
