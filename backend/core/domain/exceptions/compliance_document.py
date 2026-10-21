from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
)


class DocumentTypeError(SafetyMainDomainError):
    """Base error for the DocumentType catalog."""


class DocumentTypeNotFound(DocumentTypeError):
    def __init__(self, document_type_id: DocumentTypeId) -> None:
        self.document_type_id = document_type_id
        super().__init__(f"Document type was not found: {document_type_id.value}.")


class DuplicateDocumentTypeCode(DocumentTypeError):
    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(f"Document type code already exists in organization: {code}.")


class ComplianceDocumentError(SafetyMainDomainError):
    """Base error for ComplianceDocument aggregate invariants."""


class ComplianceDocumentNotFound(ComplianceDocumentError):
    def __init__(self, document_id: ComplianceDocumentId) -> None:
        self.document_id = document_id
        super().__init__(f"Compliance document was not found: {document_id.value}.")


class DuplicateActiveComplianceDocumentCode(ComplianceDocumentError):
    """Another active or under-review document already uses the code (D9)."""

    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(
            f"An active compliance document already uses the code: {code}."
        )


class InvalidComplianceDocumentTransition(ComplianceDocumentError):
    def __init__(
        self, *, document_id: ComplianceDocumentId, source: str, target: str
    ) -> None:
        self.document_id = document_id
        self.source = source
        self.target = target
        super().__init__(
            f"Invalid compliance document lifecycle transition: {source} -> {target}."
        )


class ComplianceDocumentValidationError(ComplianceDocumentError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ComplianceDocumentVersionConflict(ComplianceDocumentError):
    def __init__(
        self,
        *,
        document_id: ComplianceDocumentId,
        expected_version: int,
        actual_version: int,
    ) -> None:
        self.document_id = document_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Compliance document version conflict: "
            f"expected {expected_version}, actual {actual_version}."
        )


class ComplianceDocumentCannotBeModified(ComplianceDocumentError):
    def __init__(self, document_id: ComplianceDocumentId, *, reason: str) -> None:
        self.document_id = document_id
        self.reason = reason
        super().__init__(f"Compliance document cannot be modified: {reason}.")


class ComplianceDocumentReasonRequired(ComplianceDocumentError):
    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"{action} reason is required.")
