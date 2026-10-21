from __future__ import annotations

from backend.core.application.handlers.compliance_documents.create_compliance_document import (
    CreateComplianceDocumentHandler,
)
from backend.core.application.handlers.compliance_documents.files import (
    ComplianceDocumentDownloadDescriptor,
    ComplianceDocumentUploadDescriptor,
    ConfirmComplianceDocumentFileHandler,
    CreateComplianceDocumentUploadUrlHandler,
    GetComplianceDocumentDownloadUrlHandler,
    ListComplianceDocumentFilesHandler,
)
from backend.core.application.handlers.compliance_documents.get_list_compliance_documents import (
    ComplianceDocumentPageWithContext,
    ComplianceDocumentWithContext,
    GetComplianceDocumentHandler,
    ListComplianceDocumentsHandler,
)
from backend.core.application.handlers.compliance_documents.lifecycle import (
    ActivateComplianceDocumentHandler,
    ApproveComplianceDocumentHandler,
    ArchiveComplianceDocumentHandler,
    CompleteReviewComplianceDocumentHandler,
    RestoreComplianceDocumentHandler,
    StartReviewComplianceDocumentHandler,
)
from backend.core.application.handlers.compliance_documents.list_document_types import (
    ListDocumentTypesHandler,
)
from backend.core.application.handlers.compliance_documents.update_compliance_document import (
    UpdateComplianceDocumentHandler,
)

__all__ = [
    "ActivateComplianceDocumentHandler",
    "ApproveComplianceDocumentHandler",
    "ArchiveComplianceDocumentHandler",
    "ComplianceDocumentDownloadDescriptor",
    "ComplianceDocumentPageWithContext",
    "ComplianceDocumentUploadDescriptor",
    "ComplianceDocumentWithContext",
    "CompleteReviewComplianceDocumentHandler",
    "ConfirmComplianceDocumentFileHandler",
    "CreateComplianceDocumentHandler",
    "CreateComplianceDocumentUploadUrlHandler",
    "GetComplianceDocumentDownloadUrlHandler",
    "GetComplianceDocumentHandler",
    "ListComplianceDocumentFilesHandler",
    "ListComplianceDocumentsHandler",
    "ListDocumentTypesHandler",
    "RestoreComplianceDocumentHandler",
    "StartReviewComplianceDocumentHandler",
    "UpdateComplianceDocumentHandler",
]
