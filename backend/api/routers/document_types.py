from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.dependencies import (
    get_list_document_types_handler,
    require_permission,
)
from backend.api.mappers.compliance_documents import to_document_type_list_response
from backend.api.openapi import PROTECTED_BUSINESS_ERROR_RESPONSES, success_response
from backend.api.operation_ids import LIST_DOCUMENT_TYPES
from backend.api.schemas.compliance_documents import DocumentTypeListResponse
from backend.api.security import TenantContext
from backend.core.application.authorization.policies.resource_permissions import (
    COMPLIANCE_DOCUMENT_READ,
)
from backend.core.application.handlers.compliance_documents import (
    ListDocumentTypesHandler,
)
from backend.core.application.queries.compliance_documents import (
    ListDocumentTypesQuery,
)

router = APIRouter(prefix="/document-types", tags=["Document Types"])


@router.get(
    "",
    response_model=DocumentTypeListResponse,
    operation_id=LIST_DOCUMENT_TYPES,
    responses={
        **success_response(
            model=DocumentTypeListResponse,
            description="Document types listed.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_document_types(
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_READ))
    ],
    handler: Annotated[
        ListDocumentTypesHandler, Depends(get_list_document_types_handler)
    ],
    include_inactive: bool = False,
) -> DocumentTypeListResponse:
    document_types = handler.handle(
        ListDocumentTypesQuery(
            organization_id=tenant_context.organization_id,
            include_inactive=include_inactive,
        )
    )
    return to_document_type_list_response(document_types)
