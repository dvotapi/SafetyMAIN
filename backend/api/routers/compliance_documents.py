from __future__ import annotations

from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_activate_compliance_document_handler,
    get_approve_compliance_document_handler,
    get_archive_compliance_document_handler,
    get_compliance_document_id,
    get_complete_review_compliance_document_handler,
    get_confirm_compliance_document_file_handler,
    get_create_compliance_document_handler,
    get_create_compliance_document_upload_url_handler,
    get_get_compliance_document_download_url_handler,
    get_get_compliance_document_handler,
    get_list_compliance_document_files_handler,
    get_list_compliance_documents_handler,
    get_restore_compliance_document_handler,
    get_start_review_compliance_document_handler,
    get_update_compliance_document_handler,
    require_permission,
)
from backend.api.mappers.compliance_documents import (
    from_applicability_payload,
    to_compliance_document_list_response,
    to_compliance_document_response,
    to_compliance_document_response_from_context,
    to_file_response,
    update_fields_from_request,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    ACTIVATE_COMPLIANCE_DOCUMENT,
    APPROVE_COMPLIANCE_DOCUMENT,
    ARCHIVE_COMPLIANCE_DOCUMENT,
    COMPLETE_REVIEW_COMPLIANCE_DOCUMENT,
    CONFIRM_COMPLIANCE_DOCUMENT_FILE,
    CREATE_COMPLIANCE_DOCUMENT,
    CREATE_COMPLIANCE_DOCUMENT_UPLOAD_URL,
    GET_COMPLIANCE_DOCUMENT,
    GET_COMPLIANCE_DOCUMENT_DOWNLOAD_URL,
    LIST_COMPLIANCE_DOCUMENTS,
    LIST_COMPLIANCE_DOCUMENT_FILE_VERSIONS,
    RESTORE_COMPLIANCE_DOCUMENT,
    START_REVIEW_COMPLIANCE_DOCUMENT,
    UPDATE_COMPLIANCE_DOCUMENT,
)
from backend.api.schemas.compliance_documents import (
    ActivateComplianceDocumentRequest,
    ApproveComplianceDocumentRequest,
    ArchiveComplianceDocumentRequest,
    ComplianceDocumentDownloadUrlResponse,
    ComplianceDocumentFilesListResponse,
    ComplianceDocumentListResponse,
    ComplianceDocumentResponse,
    ComplianceDocumentUploadUrlRequest,
    ComplianceDocumentUploadUrlResponse,
    CompleteReviewComplianceDocumentRequest,
    ConfirmComplianceDocumentFileRequest,
    CreateComplianceDocumentRequest,
    RestoreComplianceDocumentRequest,
    StartReviewComplianceDocumentRequest,
    UpdateComplianceDocumentRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    COMPLIANCE_DOCUMENT_ACTIVATE,
    COMPLIANCE_DOCUMENT_APPROVE,
    COMPLIANCE_DOCUMENT_ARCHIVE,
    COMPLIANCE_DOCUMENT_CREATE,
    COMPLIANCE_DOCUMENT_READ,
    COMPLIANCE_DOCUMENT_UPDATE,
)
from backend.core.application.handlers.compliance_documents import (
    ActivateComplianceDocumentHandler,
    ApproveComplianceDocumentHandler,
    ArchiveComplianceDocumentHandler,
    CompleteReviewComplianceDocumentHandler,
    ConfirmComplianceDocumentFileHandler,
    CreateComplianceDocumentUploadUrlHandler,
    GetComplianceDocumentDownloadUrlHandler,
    ListComplianceDocumentFilesHandler,
    RestoreComplianceDocumentHandler,
    StartReviewComplianceDocumentHandler,
)
from backend.core.application.commands.compliance_document_files import (
    ConfirmComplianceDocumentFileCommand,
    CreateComplianceDocumentUploadUrlCommand,
)
from backend.core.application.commands.compliance_document_lifecycle import (
    ActivateComplianceDocumentCommand,
    ApproveComplianceDocumentCommand,
    ArchiveComplianceDocumentCommand,
    CompleteReviewComplianceDocumentCommand,
    RestoreComplianceDocumentCommand,
    StartReviewComplianceDocumentCommand,
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


@router.post(
    "/{document_id}/approve",
    response_model=ComplianceDocumentResponse,
    operation_id=APPROVE_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document approved.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def approve_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: ApproveComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_APPROVE))
    ],
    handler: Annotated[
        ApproveComplianceDocumentHandler,
        Depends(get_approve_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        ApproveComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.post(
    "/{document_id}/activate",
    response_model=ComplianceDocumentResponse,
    operation_id=ACTIVATE_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document activated.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def activate_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: ActivateComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_ACTIVATE))
    ],
    handler: Annotated[
        ActivateComplianceDocumentHandler,
        Depends(get_activate_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        ActivateComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.post(
    "/{document_id}/start-review",
    response_model=ComplianceDocumentResponse,
    operation_id=START_REVIEW_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document review started.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def start_review_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: StartReviewComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_UPDATE))
    ],
    handler: Annotated[
        StartReviewComplianceDocumentHandler,
        Depends(get_start_review_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        StartReviewComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.post(
    "/{document_id}/complete-review",
    response_model=ComplianceDocumentResponse,
    operation_id=COMPLETE_REVIEW_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document review completed.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def complete_review_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: CompleteReviewComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_ACTIVATE))
    ],
    handler: Annotated[
        CompleteReviewComplianceDocumentHandler,
        Depends(get_complete_review_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        CompleteReviewComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            completed_on=request_body.completed_on,
            next_review_at=request_body.next_review_at,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.post(
    "/{document_id}/archive",
    response_model=ComplianceDocumentResponse,
    operation_id=ARCHIVE_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document archived.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def archive_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: ArchiveComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_ARCHIVE))
    ],
    handler: Annotated[
        ArchiveComplianceDocumentHandler,
        Depends(get_archive_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        ArchiveComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            reason=request_body.reason,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.post(
    "/{document_id}/restore",
    response_model=ComplianceDocumentResponse,
    operation_id=RESTORE_COMPLIANCE_DOCUMENT,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Compliance document restored.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def restore_compliance_document(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: RestoreComplianceDocumentRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_ARCHIVE))
    ],
    handler: Annotated[
        RestoreComplianceDocumentHandler,
        Depends(get_restore_compliance_document_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        RestoreComplianceDocumentCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            reason=request_body.reason,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.post(
    "/{document_id}/files/upload-url",
    response_model=ComplianceDocumentUploadUrlResponse,
    operation_id=CREATE_COMPLIANCE_DOCUMENT_UPLOAD_URL,
    responses={
        **success_response(
            model=ComplianceDocumentUploadUrlResponse,
            description="Presigned upload URL issued.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_compliance_document_upload_url(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: ComplianceDocumentUploadUrlRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_UPDATE))
    ],
    handler: Annotated[
        CreateComplianceDocumentUploadUrlHandler,
        Depends(get_create_compliance_document_upload_url_handler),
    ],
) -> ComplianceDocumentUploadUrlResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    descriptor = handler.handle(
        CreateComplianceDocumentUploadUrlCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            filename=request_body.filename,
            content_type=request_body.content_type,
            size_bytes=request_body.size_bytes,
            sha256=request_body.sha256,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return ComplianceDocumentUploadUrlResponse(
        upload_id=descriptor.upload_id,
        bucket=descriptor.bucket,
        key=descriptor.key,
        url=descriptor.presigned.url,
        method=descriptor.presigned.method,
        headers=descriptor.presigned.headers,
        expires_at=descriptor.presigned.expires_at,
    )


@router.post(
    "/{document_id}/files/confirm",
    response_model=ComplianceDocumentResponse,
    operation_id=CONFIRM_COMPLIANCE_DOCUMENT_FILE,
    responses={
        **success_response(
            model=ComplianceDocumentResponse,
            description="Uploaded file attached to the document.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def confirm_compliance_document_file(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    request_body: ConfirmComplianceDocumentFileRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_UPDATE))
    ],
    handler: Annotated[
        ConfirmComplianceDocumentFileHandler,
        Depends(get_confirm_compliance_document_file_handler),
    ],
) -> ComplianceDocumentResponse:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    result = handler.handle(
        ConfirmComplianceDocumentFileCommand(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            key=request_body.key,
            size_bytes=request_body.size_bytes,
            sha256=request_body.sha256,
            content_type=request_body.content_type,
            original_filename=request_body.original_filename,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_compliance_document_response_from_context(result)


@router.get(
    "/{document_id}/files/current/download-url",
    response_model=ComplianceDocumentDownloadUrlResponse,
    operation_id=GET_COMPLIANCE_DOCUMENT_DOWNLOAD_URL,
    responses={
        **success_response(
            model=ComplianceDocumentDownloadUrlResponse,
            description="Presigned download URL issued.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_compliance_document_download_url(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_READ))
    ],
    handler: Annotated[
        GetComplianceDocumentDownloadUrlHandler,
        Depends(get_get_compliance_document_download_url_handler),
    ],
) -> ComplianceDocumentDownloadUrlResponse:
    descriptor = handler.handle(
        GetComplianceDocumentQuery(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
        )
    )
    return ComplianceDocumentDownloadUrlResponse(
        url=descriptor.url,
        expires_at=descriptor.expires_at,
        filename=descriptor.file.original_filename,
        content_type=descriptor.file.content_type,
        size_bytes=descriptor.file.size_bytes,
        sha256=descriptor.file.sha256,
    )


@router.get(
    "/{document_id}/files/versions",
    response_model=ComplianceDocumentFilesListResponse,
    operation_id=LIST_COMPLIANCE_DOCUMENT_FILE_VERSIONS,
    responses={
        **success_response(
            model=ComplianceDocumentFilesListResponse,
            description="Compliance document file versions listed.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_compliance_document_file_versions(
    document_id: Annotated[ComplianceDocumentId, Depends(get_compliance_document_id)],
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_READ))
    ],
    handler: Annotated[
        ListComplianceDocumentFilesHandler,
        Depends(get_list_compliance_document_files_handler),
    ],
) -> ComplianceDocumentFilesListResponse:
    files = handler.handle(
        GetComplianceDocumentQuery(
            organization_id=tenant_context.organization_id,
            document_id=document_id,
        )
    )
    return ComplianceDocumentFilesListResponse(
        items=[to_file_response(file) for file in files]
    )
