"""Attach one scanned PDF to a place through the existing handlers (§4.5, plan S1, S4).

Each step runs in its own unit of work and records its own audit events:

1. develop: draft document + link to the place;
2. set ``effective_from`` (activation requires it, plan S5);
3. upload URL, then a PUT of the bytes (by the caller's ``put``), then confirm;
4. approve;
5. activate.

A failure stops this place at that step. Nothing is rolled back or deleted:
the place keeps its linked draft (or approved) document, and a re-run skips it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
)
from backend.core.application.commands.compliance_document_files import (
    ConfirmComplianceDocumentFileCommand,
    CreateComplianceDocumentUploadUrlCommand,
)
from backend.core.application.commands.compliance_document_lifecycle import (
    ActivateComplianceDocumentCommand,
    ApproveComplianceDocumentCommand,
)
from backend.core.application.commands.compliance_documents import (
    UpdateComplianceDocumentCommand,
)
from backend.core.application.commands.shelf import DevelopShelfSlotDocumentCommand
from backend.core.application.handlers.compliance_documents import (
    ActivateComplianceDocumentHandler,
    ApproveComplianceDocumentHandler,
    ConfirmComplianceDocumentFileHandler,
    CreateComplianceDocumentUploadUrlHandler,
    UpdateComplianceDocumentHandler,
)
from backend.core.application.handlers.shelf.slots import (
    DevelopShelfSlotDocumentHandler,
)
from backend.core.application.services.shelf_scan_attachment import AttachCandidate
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.storage import PresignedUpload, StorageContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects import OrganizationId, UserId

PDF_CONTENT_TYPE = "application/pdf"


@dataclass(frozen=True, slots=True)
class AttachOutcome:
    code: str
    attached: bool
    document_id: str | None = None
    failed_step: str | None = None
    error: str = ""


class AttachShelfScanHandler:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWorkContract],
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
        storage: StorageContract,
        max_upload_bytes: int,
        read_bytes: Callable[[str], bytes],
        put: Callable[[PresignedUpload, bytes], None],
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._audit = audit
        self._storage = storage
        self._max_upload_bytes = max_upload_bytes
        self._read_bytes = read_bytes
        self._put = put

    def handle(
        self,
        candidate: AttachCandidate,
        *,
        organization_id: OrganizationId,
        actor_id: UserId,
        effective_from: date,
    ) -> AttachOutcome:
        slot = candidate.slot
        code = slot.code.value
        context = AuditContext(actor_user_id=actor_id, authorization_organization_id=organization_id)
        step = "develop"
        document_id = None
        try:
            with self._uow_factory() as uow:
                developed = DevelopShelfSlotDocumentHandler(uow, self._clock, self._audit).handle(
                    DevelopShelfSlotDocumentCommand(
                        organization_id=organization_id,
                        slot_id=slot.id,
                        actor_id=actor_id,
                        expected_version=slot.version,
                        document_type_code=candidate.document_type.code,
                        audit_context=context,
                    )
                )
            document = developed.document
            document_id = document.id

            step = "effective_from"
            with self._uow_factory() as uow:
                document = UpdateComplianceDocumentHandler(uow, self._clock, self._audit).handle(
                    UpdateComplianceDocumentCommand(
                        organization_id=organization_id,
                        document_id=document.id,
                        actor_id=actor_id,
                        expected_version=document.version,
                        effective_from=effective_from,
                        audit_context=context,
                    )
                )

            step = "upload"
            data = self._read_bytes(candidate.file.path)
            sha256 = hashlib.sha256(data).hexdigest()
            filename = candidate.file.path.replace("\\", "/").rsplit("/", 1)[-1]
            with self._uow_factory() as uow:
                descriptor = CreateComplianceDocumentUploadUrlHandler(
                    uow, self._storage, self._max_upload_bytes, self._audit
                ).handle(
                    CreateComplianceDocumentUploadUrlCommand(
                        organization_id=organization_id,
                        document_id=document.id,
                        actor_id=actor_id,
                        filename=filename,
                        content_type=PDF_CONTENT_TYPE,
                        size_bytes=len(data),
                        sha256=sha256,
                        audit_context=context,
                    )
                )
            self._put(descriptor.presigned, data)

            step = "confirm"
            with self._uow_factory() as uow:
                confirmed = ConfirmComplianceDocumentFileHandler(
                    uow, self._storage, self._clock, self._audit
                ).handle(
                    ConfirmComplianceDocumentFileCommand(
                        organization_id=organization_id,
                        document_id=document.id,
                        actor_id=actor_id,
                        expected_version=document.version,
                        key=descriptor.key,
                        size_bytes=len(data),
                        sha256=sha256,
                        content_type=PDF_CONTENT_TYPE,
                        original_filename=filename,
                        audit_context=context,
                    )
                )
            document = confirmed.document

            step = "approve"
            with self._uow_factory() as uow:
                document = ApproveComplianceDocumentHandler(uow, self._clock, self._audit).handle(
                    ApproveComplianceDocumentCommand(
                        organization_id=organization_id,
                        document_id=document.id,
                        actor_id=actor_id,
                        expected_version=document.version,
                        audit_context=context,
                    )
                ).document

            step = "activate"
            with self._uow_factory() as uow:
                ActivateComplianceDocumentHandler(uow, self._clock, self._audit).handle(
                    ActivateComplianceDocumentCommand(
                        organization_id=organization_id,
                        document_id=document.id,
                        actor_id=actor_id,
                        expected_version=document.version,
                        audit_context=context,
                    )
                )
        except Exception as error:  # noqa: BLE001 - reported per place, the run continues
            return AttachOutcome(
                code=code,
                attached=False,
                document_id=str(document_id.value) if document_id else None,
                failed_step=step,
                error=f"{type(error).__name__}: {error}"[:200],
            )
        return AttachOutcome(code=code, attached=True, document_id=str(document_id.value))
