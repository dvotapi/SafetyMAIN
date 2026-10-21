from __future__ import annotations

from backend.core.application.handlers.compliance_documents.create_compliance_document import (
    CreateComplianceDocumentHandler,
)
from backend.core.application.handlers.compliance_documents.get_list_compliance_documents import (
    GetComplianceDocumentHandler,
    ListComplianceDocumentsHandler,
)
from backend.core.application.handlers.compliance_documents.list_document_types import (
    ListDocumentTypesHandler,
)
from backend.core.application.handlers.compliance_documents.update_compliance_document import (
    UpdateComplianceDocumentHandler,
)

__all__ = [
    "CreateComplianceDocumentHandler",
    "GetComplianceDocumentHandler",
    "ListComplianceDocumentsHandler",
    "ListDocumentTypesHandler",
    "UpdateComplianceDocumentHandler",
]
