from __future__ import annotations

from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_compliance_document_id,
    get_create_compliance_document_handler,
    get_get_compliance_document_handler,
    get_list_compliance_documents_handler,
    get_update_compliance_document_handler,
    require_permission,
)
from backend.api.mappers.compliance_documents import (
    from_applicability_payload,
    to_compliance_document_list_response,
    to_compliance_document_response,
    to_compliance_document_response_from_context,
    update_fields_from_request,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    CREATE_COMPLIANCE_DOCUMENT,
    GET_COMPLIANCE_DOCUMENT,
    LIST_COMPLIANCE_DOCUMENTS,
    UPDATE_COMPLIANCE_DOCUMENT,
)
from backend.api.schemas.compliance_documents import (
    ComplianceDocumentListResponse,
    ComplianceDocumentResponse,
    CreateComplianceDocumentRequest,
    UpdateComplianceDocumentRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    COMPLIANCE_DOCUMENT_CREATE,
    COMPLIANCE_DOCUMENT_READ,
    COMPLIANCE_DOCUMENT_UPDATE,
)
from backend.core.application.commands.compliance_documents import (
    CreateComplianceDocumentCommand,
    UpdateComplianceDocumentCommand,
)
from backend.core.application.exceptions.authentication import UnauthenticatedError
from backend.core.application.handlers.compliance_documents import (
    CreateComplianceDocumentHandler,
    GetComplianceDocumentHandler,
    ListComplianceDocumentsHandler,
    UpdateComplianceDocumentHandler,
)
from backend.core.application.queries.compliance_documents import (
    GetComplianceDocumentQuery,
    ListComplianceDocumentsQuery,
)
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentSource,
    ComplianceDocumentStatus,
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
)


def _parse_enum_param[EnumT: Enum](
    raw: str | None, enum_cls: type[EnumT], field_name: str
) -> EnumT | None:
    """Map an unknown query enum value to 422 instead of an unhandled 500."""
    if raw is None:
        return None
    try:
        return enum_cls(raw)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_cls)
        raise RequestValidationError(
            [
                {
                    "loc": ("query", field_name),
                    "msg": f"Value must be one of: {allowed}.",
                    "type": "value_error.enum",
                }
            ]
        ) from exc


router = APIRouter(prefix="/compliance-documents", tags=["Compliance Documents"])


@router.post(
    "",
    response_model=ComplianceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_COMPLIANCE_DOCUMENT,
    responses={
        **created_response(
            model=ComplianceDocumentResponse,
            description="Compliance document created.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_compliance_document(
    request_body: CreateComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_CREATE))
    ],
    handler: Annotated[
        CreateComplianceDocumentHandler,
        Depends(get_create_compliance_document_handler),
    ],
) -> JSONResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    document = handler.handle(
        CreateComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            actor_id=tenant_context.actor_user_id,
            document_type_id=DocumentTypeId(value=request_body.document_type_id),
            code=request_body.code,
            title=request_body.title,
            subject_id=request_body.subject_id,
            issued_at=request_body.issued_at,
            effective_from=request_body.effective_from,
            next_review_at=request_body.next_review_at,
            approved_by_document_id=(
                None
                if request_body.approved_by_document_id is None
                else ComplianceDocumentId(value=request_body.approved_by_document_id)
            ),
            supersedes_document_id=(
                None
                if request_body.supersedes_document_id is None
                else ComplianceDocumentId(value=request_body.supersedes_document_id)
            ),
            applicability=from_applicability_payload(request_body.applicability),
            source=ComplianceDocumentSource(request_body.source),
            notes=request_body.notes,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    body = to_compliance_document_response(document, is_review_due=False)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=body.model_dump(mode="json"),
        headers={
            "Location": f"{API_V1_PREFIX}/compliance-documents/{document.id.value}"
        },
    )


@router.get(
    "",
    response_model=ComplianceDocumentListResponse,
    operation_id=LIST_COMPLIANCE_DOCUMENTS,
    responses={
        **success_response(
            model=ComplianceDocumentListResponse,
            description="Compliance documents listed.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_compliance_documents(
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_READ))
    ],
    handler: Annotated[
        ListComplianceDocumentsHandler,
        Depends(get_list_compliance_documents_handler),
    ],
    document_type_id: Annotated[list[UUID] | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    subject_kind: str | None = None,
    safety_domain: str | None = None,
    review_due: bool | None = None,
    include_archived: bool = False,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ComplianceDocumentListResponse:
    page = handler.handle(
        ListComplianceDocumentsQuery(
            organization_id=tenant_context.organization_id,
            document_type_ids=tuple(
                DocumentTypeId(value=item) for item in (document_type_id or ())
            ),
            status=_parse_enum_param(status_filter, ComplianceDocumentStatus, "status"),
            subject_kind=_parse_enum_param(
                subject_kind, DocumentSubjectKind, "subject_kind"
            ),
            safety_domain=_parse_enum_param(
                safety_domain, SafetyDomain, "safety_domain"
            ),
            review_due=review_due,
            include_archived=include_archived,
            search=search,
            offset=offset,
            limit=limit,
        )
    )
    return to_compliance_document_list_response(page)


@router.get(
    "/{document_id}",
    response_model=ComplianceDocumentResponse,
    operation_id=GET_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document retrieved.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_READ))
    ],
    handler: Annotated[
        GetComplianceDocumentHandler, Depends(get_get_compliance_document_handler)
    ],
) -> ComplianceDocumentResponse:
    item = handler.handle(
        GetComplianceDocumentQuery(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
        )
    )
    return to_compliance_document_response_from_context(item)


@router.patch(
    "/{document_id}",
    response_model=ComplianceDocumentResponse,
    operation_id=UPDATE_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document updated.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: UpdateComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_UPDATE))
    ],
    handler: Annotated[
        UpdateComplianceDocumentHandler,
        Depends(get_update_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    nullable_kwargs = update_fields_from_request(request_body)
    approved_by_raw = nullable_kwargs.pop("approved_by_document_id")
    supersedes_raw = nullable_kwargs.pop("supersedes_document_id")
    approved_by = _wrap_document_id(approved_by_raw)
    supersedes = _wrap_document_id(supersedes_raw)
    document = handler.handle(
        UpdateComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            code=request_body.code,
            title=request_body.title,
            applicability=from_applicability_payload(request_body.applicability),
            notes=request_body.notes,
            approved_by_document_id=approved_by,
            supersedes_document_id=supersedes,
            audit_context=AuditContext.from_tenant(tenant_context),
            **nullable_kwargs,
        )
    )
    return to_compliance_document_response(document, is_review_due=False)


def _wrap_document_id(raw: object) -> object:
    """Keep the UNSET sentinel; wrap a UUID in ``ComplianceDocumentId``."""
    from backend.core.application.commands.compliance_documents import UNSET

    if raw is UNSET or raw is None:
        return raw
    assert isinstance(raw, UUID)
    return ComplianceDocumentId(value=raw)
