"""Signed scans on ComplianceDocument (TASK-P11-012 D1, P11-001 amendments A2–A3)."""

from __future__ import annotations

import pytest

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentCannotBeModified,
    ComplianceDocumentValidationError,
    ComplianceDocumentVersionConflict,
)
from backend.core.domain.value_objects.compliance_enums import DocumentFileRole
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    advance_to_active,
    advance_to_approved,
    compliance_document_draft,
    make_document_file,
    make_document_type,
    with_file,
)


def _scan(document: ComplianceDocument, *, content_type: str = "application/pdf"):
    return make_document_file(document, filename="scan.pdf").model_copy(
        update={"role": DocumentFileRole.SIGNED_SCAN, "content_type": content_type}
    )


def _attach(document: ComplianceDocument, **kwargs) -> ComplianceDocument:
    return document.attach_signed_scan(
        file=_scan(document, **kwargs),
        at=FIXED_AT,
        actor_id=document.created_by,
        expected_version=document.version,
    )


def test_current_file_is_the_last_working_file_and_scans_are_separate() -> None:
    document_type = make_document_type()
    active = advance_to_active(compliance_document_draft(document_type), document_type)
    working = active.current_file

    scanned = _attach(active)
    rescanned = _attach(scanned, content_type="image/jpeg")

    assert scanned.current_file == working
    assert scanned.current_signed_scan is not None
    assert rescanned.current_file == working
    assert rescanned.current_signed_scan is not None
    assert rescanned.current_signed_scan.content_type == "image/jpeg"
    assert len(rescanned.files) == 3
    assert rescanned.version == active.version + 2


@pytest.mark.parametrize("stage", ["approved", "active", "under_review"])
def test_signed_scan_allowed_statuses(stage: str) -> None:
    document_type = make_document_type()
    draft = compliance_document_draft(document_type)
    if stage == "approved":
        document = advance_to_approved(draft)
    else:
        document = advance_to_active(draft, document_type)
        if stage == "under_review":
            document = document.start_review(
                at=FIXED_AT, actor_id=document.created_by, expected_version=document.version
            )

    assert _attach(document).current_signed_scan is not None


def test_signed_scan_refused_in_draft_and_for_wrong_files() -> None:
    document_type = make_document_type()
    draft = compliance_document_draft(document_type)
    active = advance_to_active(draft, document_type)

    with pytest.raises(ComplianceDocumentCannotBeModified):
        _attach(draft)
    with pytest.raises(ComplianceDocumentValidationError):
        _attach(active, content_type="application/vnd.ms-excel")
    with pytest.raises(ComplianceDocumentValidationError):
        active.attach_signed_scan(
            file=make_document_file(active),
            at=FIXED_AT,
            actor_id=active.created_by,
            expected_version=active.version,
        )
    with pytest.raises(ComplianceDocumentVersionConflict):
        active.attach_signed_scan(
            file=_scan(active), at=FIXED_AT, actor_id=active.created_by, expected_version=99
        )


def test_attach_file_refuses_a_signed_scan() -> None:
    draft = compliance_document_draft()

    with pytest.raises(ComplianceDocumentValidationError):
        draft.attach_file(
            file=_scan(draft), at=FIXED_AT, actor_id=draft.created_by, expected_version=1
        )


def test_a_signed_scan_does_not_satisfy_the_approval_precondition() -> None:
    draft = compliance_document_draft()

    with pytest.raises(ComplianceDocumentValidationError):
        draft.approve(at=FIXED_AT, actor_id=draft.created_by, expected_version=1)
    assert with_file(draft).current_file is not None
