from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentCannotBeModified,
    ComplianceDocumentReasonRequired,
    ComplianceDocumentValidationError,
    ComplianceDocumentVersionConflict,
    InvalidComplianceDocumentTransition,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentApplicability,
    DocumentFile,
)
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentSource,
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    SHA256_HEX,
    advance_to_active,
    advance_to_approved,
    compliance_document_draft,
    make_actor,
    make_document_file,
    make_document_type,
    rich_applicability,
    with_file,
)

LATER = FIXED_AT + timedelta(hours=1)


def _archive(document: ComplianceDocument) -> ComplianceDocument:
    return document.archive(
        at=LATER,
        actor_id=document.created_by,
        expected_version=document.version,
        reason="Replaced by a corporate standard",
    )


def _under_review(document: ComplianceDocument) -> ComplianceDocument:
    return document.start_review(
        at=LATER, actor_id=document.created_by, expected_version=document.version
    )


# --- creation -----------------------------------------------------------------


def test_create_starts_as_draft_and_copies_subject_kind_from_type() -> None:
    document_type = make_document_type()
    actor = make_actor()

    document = compliance_document_draft(
        document_type,
        code="  ИОТ-012 ",
        title="  Инструкция ",
        created_by=actor,
        issued_at=date(2026, 9, 20),
        notes="  Initial edition ",
    )

    assert document.status is ComplianceDocumentStatus.DRAFT
    assert document.organization_id == document_type.organization_id
    assert document.document_type_id == document_type.id
    assert document.subject_kind is DocumentSubjectKind.ORGANIZATION
    assert document.subject_id is None
    assert document.code == "ИОТ-012"
    assert document.title == "Инструкция"
    assert document.notes == "Initial edition"
    assert document.issued_at == date(2026, 9, 20)
    assert document.effective_from == date(2026, 10, 1)
    assert document.next_review_at is None
    assert document.source is ComplianceDocumentSource.MANUAL
    assert document.applicability == DocumentApplicability()
    assert document.files == ()
    assert document.current_file is None
    assert document.version == 1
    assert document.created_by == actor
    assert document.updated_by == actor
    assert document.created_at == FIXED_AT
    assert document.updated_at == FIXED_AT


@pytest.mark.parametrize(
    "overrides",
    [{"code": "  "}, {"code": "x" * 65}, {"title": " "}],
)
def test_create_requires_code_and_title(overrides: dict[str, Any]) -> None:
    with pytest.raises(ComplianceDocumentValidationError):
        compliance_document_draft(**overrides)


def test_create_rejects_type_of_another_organization() -> None:
    document_type = make_document_type()

    with pytest.raises(ComplianceDocumentValidationError):
        ComplianceDocument.create(
            organization_id=OrganizationId(value=uuid4()),
            document_type=document_type,
            code="ИОТ-1",
            title="Инструкция",
            created_by=make_actor(),
            created_at=FIXED_AT,
        )


def test_create_rejects_inactive_type() -> None:
    with pytest.raises(ComplianceDocumentValidationError):
        compliance_document_draft(make_document_type(is_active=False))


def test_organization_subject_must_not_have_subject_id() -> None:
    with pytest.raises(ComplianceDocumentValidationError):
        compliance_document_draft(subject_id=uuid4())


def test_employee_subject_requires_subject_id() -> None:
    document_type = make_document_type(
        code="driver_license",
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        review_period_months=None,
        validity_months=120,
    )

    with pytest.raises(ComplianceDocumentValidationError):
        compliance_document_draft(document_type)

    employee_id = uuid4()
    document = compliance_document_draft(document_type, subject_id=employee_id)
    assert document.subject_kind is DocumentSubjectKind.EMPLOYEE
    assert document.subject_id == employee_id


def test_create_rejects_self_references() -> None:
    document_id = ComplianceDocumentId(value=uuid4())

    with pytest.raises(ComplianceDocumentValidationError):
        compliance_document_draft(document_id=document_id, supersedes_document_id=document_id)
    with pytest.raises(ComplianceDocumentValidationError):
        compliance_document_draft(
            document_id=document_id, approved_by_document_id=document_id
        )


def test_applicability_strips_values_and_rejects_blank_entries() -> None:
    applicability = DocumentApplicability(positions=("  Водитель ",))
    assert applicability.positions == ("Водитель",)

    with pytest.raises(ValueError):
        DocumentApplicability(departments=("  ",))


# --- files and draft editing ---------------------------------------------------


def test_attach_file_in_draft_appends_history_and_sets_current_file() -> None:
    document = compliance_document_draft()
    first = make_document_file(document, filename="v1.pdf")
    second = make_document_file(document, filename="v2.pdf")

    once = document.attach_file(
        file=first, at=LATER, actor_id=document.created_by, expected_version=1
    )
    twice = once.attach_file(
        file=second, at=LATER, actor_id=document.created_by, expected_version=2
    )

    assert twice.files == (first, second)
    assert twice.current_file == second
    assert twice.version == 3
    assert twice.updated_at == LATER


def test_attach_file_rejects_the_same_key_twice() -> None:
    document = compliance_document_draft()
    file = make_document_file(document)
    once = document.attach_file(
        file=file, at=LATER, actor_id=document.created_by, expected_version=1
    )

    with pytest.raises(ComplianceDocumentValidationError):
        once.attach_file(
            file=file.model_copy(update={"original_filename": "copy.pdf"}),
            at=LATER,
            actor_id=document.created_by,
            expected_version=2,
        )


def test_attach_file_only_in_draft() -> None:
    approved = advance_to_approved(compliance_document_draft())

    with pytest.raises(ComplianceDocumentCannotBeModified):
        approved.attach_file(
            file=make_document_file(approved),
            at=LATER,
            actor_id=approved.created_by,
            expected_version=approved.version,
        )


def test_document_file_validates_metadata() -> None:
    document = compliance_document_draft()
    file = make_document_file(document)
    assert file.sha256 == SHA256_HEX

    upper = file.model_validate({**file.model_dump(), "sha256": "A" * 64})
    assert upper.sha256 == "a" * 64
    for update in (
        {"sha256": "z" * 64},
        {"sha256": "a" * 63},
        {"size_bytes": 0},
        {"key": " "},
        {"original_filename": ""},
    ):
        with pytest.raises(ValueError):
            DocumentFile.model_validate({**file.model_dump(), **update})


def test_update_details_in_draft_sets_and_clears_fields() -> None:
    document_type = make_document_type()
    order_id = ComplianceDocumentId(value=uuid4())
    document = compliance_document_draft(
        document_type,
        approved_by_document_id=order_id,
        next_review_at=date(2031, 10, 1),
    )
    applicability = rich_applicability()

    updated = document.update_details(
        at=LATER,
        actor_id=make_actor(),
        expected_version=1,
        code="ИОТ-013",
        title="Новая редакция",
        issued_at=date(2026, 9, 1),
        effective_from=None,
        next_review_at=None,
        approved_by_document_id=None,
        applicability=applicability,
        notes="Edited",
    )

    assert updated.code == "ИОТ-013"
    assert updated.title == "Новая редакция"
    assert updated.issued_at == date(2026, 9, 1)
    assert updated.effective_from is None
    assert updated.next_review_at is None
    assert updated.approved_by_document_id is None
    assert updated.applicability == applicability
    assert updated.notes == "Edited"
    assert updated.version == 2
    assert updated.updated_at == LATER


def test_update_details_leaves_omitted_fields_unchanged() -> None:
    order_id = ComplianceDocumentId(value=uuid4())
    document = compliance_document_draft(approved_by_document_id=order_id)

    updated = document.update_details(
        at=LATER, actor_id=document.created_by, expected_version=1, title="Renamed"
    )

    assert updated.title == "Renamed"
    assert updated.code == document.code
    assert updated.effective_from == document.effective_from
    assert updated.approved_by_document_id == order_id


def test_update_details_can_change_type_with_same_subject_kind() -> None:
    document = compliance_document_draft()
    other_type = make_document_type(
        organization_id=document.organization_id, code="production_instruction"
    )

    updated = document.update_details(
        at=LATER,
        actor_id=document.created_by,
        expected_version=1,
        document_type=other_type,
    )

    assert updated.document_type_id == other_type.id


@pytest.mark.parametrize(
    "type_overrides",
    [
        {"is_active": False},
        {"subject_kind": DocumentSubjectKind.EMPLOYEE},
        {"organization_id": OrganizationId(value=uuid4())},
    ],
)
def test_update_details_rejects_incompatible_type(type_overrides: dict[str, Any]) -> None:
    document = compliance_document_draft()
    overrides: dict[str, Any] = {
        "organization_id": document.organization_id,
        **type_overrides,
    }
    other_type = make_document_type(code="other", **overrides)

    with pytest.raises(ComplianceDocumentValidationError):
        document.update_details(
            at=LATER,
            actor_id=document.created_by,
            expected_version=1,
            document_type=other_type,
        )


def test_update_details_rejects_blank_title_and_self_reference() -> None:
    document = compliance_document_draft()

    with pytest.raises(ComplianceDocumentValidationError):
        document.update_details(
            at=LATER, actor_id=document.created_by, expected_version=1, title=" "
        )
    with pytest.raises(ComplianceDocumentValidationError):
        document.update_details(
            at=LATER,
            actor_id=document.created_by,
            expected_version=1,
            supersedes_document_id=document.id,
        )


def test_update_details_only_in_draft() -> None:
    approved = advance_to_approved(compliance_document_draft())

    with pytest.raises(ComplianceDocumentCannotBeModified):
        approved.update_details(
            at=LATER,
            actor_id=approved.created_by,
            expected_version=approved.version,
            title="Too late",
        )


# --- approve and activate ------------------------------------------------------


def test_approve_requires_a_current_file() -> None:
    document = compliance_document_draft()

    with pytest.raises(ComplianceDocumentValidationError):
        document.approve(at=LATER, actor_id=document.created_by, expected_version=1)

    approved = advance_to_approved(document)
    assert approved.status is ComplianceDocumentStatus.APPROVED


def test_activate_computes_next_review_from_effective_from() -> None:
    document_type = make_document_type(review_period_months=60)
    document = compliance_document_draft(document_type, effective_from=date(2024, 2, 29))

    active = advance_to_active(document, document_type)

    assert active.status is ComplianceDocumentStatus.ACTIVE
    assert active.next_review_at == date(2029, 2, 28)


def test_activate_keeps_explicit_next_review_at() -> None:
    document_type = make_document_type(review_period_months=60)
    document = compliance_document_draft(
        document_type, next_review_at=date(2027, 6, 1)
    )

    active = advance_to_active(document, document_type)

    assert active.next_review_at == date(2027, 6, 1)


def test_activate_without_review_period_leaves_next_review_empty() -> None:
    document_type = make_document_type(code="order", review_period_months=None)

    active = advance_to_active(compliance_document_draft(document_type), document_type)

    assert active.next_review_at is None


def test_activate_requires_effective_from() -> None:
    document_type = make_document_type()
    approved = advance_to_approved(
        compliance_document_draft(document_type, effective_from=None)
    )

    with pytest.raises(ComplianceDocumentValidationError):
        approved.activate(
            document_type=document_type,
            at=LATER,
            actor_id=approved.created_by,
            expected_version=approved.version,
        )


def test_activate_requires_approval_order_when_type_demands_it() -> None:
    document_type = make_document_type(requires_approval_order=True)
    approved = advance_to_approved(compliance_document_draft(document_type))

    with pytest.raises(ComplianceDocumentValidationError):
        approved.activate(
            document_type=document_type,
            at=LATER,
            actor_id=approved.created_by,
            expected_version=approved.version,
        )

    ordered = advance_to_active(
        compliance_document_draft(
            document_type,
            approved_by_document_id=ComplianceDocumentId(value=uuid4()),
        ),
        document_type,
    )
    assert ordered.status is ComplianceDocumentStatus.ACTIVE


def test_activate_rejects_a_different_document_type() -> None:
    approved = advance_to_approved(compliance_document_draft())
    other_type = make_document_type(organization_id=approved.organization_id)

    with pytest.raises(ComplianceDocumentValidationError):
        approved.activate(
            document_type=other_type,
            at=LATER,
            actor_id=approved.created_by,
            expected_version=approved.version,
        )


def test_activate_only_from_approved() -> None:
    document_type = make_document_type()
    draft = with_file(compliance_document_draft(document_type))
    under_review = _under_review(
        advance_to_active(compliance_document_draft(document_type), document_type)
    )

    for document in (draft, under_review):
        with pytest.raises(InvalidComplianceDocumentTransition):
            document.activate(
                document_type=document_type,
                at=LATER,
                actor_id=document.created_by,
                expected_version=document.version,
            )


# --- review --------------------------------------------------------------------


def test_review_cycle_with_computed_next_review() -> None:
    document_type = make_document_type(review_period_months=60)
    active = advance_to_active(compliance_document_draft(document_type), document_type)

    under_review = _under_review(active)
    assert under_review.status is ComplianceDocumentStatus.UNDER_REVIEW

    completed = under_review.complete_review(
        document_type=document_type,
        completed_on=date(2026, 1, 31),
        at=LATER,
        actor_id=active.created_by,
        expected_version=under_review.version,
    )

    assert completed.status is ComplianceDocumentStatus.ACTIVE
    assert completed.next_review_at == date(2031, 1, 31)
    assert completed.version == under_review.version + 1


def test_complete_review_uses_explicit_next_review_at() -> None:
    document_type = make_document_type(review_period_months=60)
    under_review = _under_review(
        advance_to_active(compliance_document_draft(document_type), document_type)
    )

    completed = under_review.complete_review(
        document_type=document_type,
        completed_on=date(2026, 10, 1),
        next_review_at=date(2028, 10, 1),
        at=LATER,
        actor_id=under_review.created_by,
        expected_version=under_review.version,
    )

    assert completed.next_review_at == date(2028, 10, 1)


def test_complete_review_without_review_period_clears_next_review() -> None:
    document_type = make_document_type(review_period_months=None)
    active = advance_to_active(
        compliance_document_draft(document_type, next_review_at=date(2027, 1, 1)),
        document_type,
    )
    under_review = _under_review(active)

    completed = under_review.complete_review(
        document_type=document_type,
        completed_on=date(2026, 10, 1),
        at=LATER,
        actor_id=active.created_by,
        expected_version=under_review.version,
    )

    assert completed.next_review_at is None


def test_complete_review_requires_under_review() -> None:
    document_type = make_document_type()
    active = advance_to_active(compliance_document_draft(document_type), document_type)

    with pytest.raises(InvalidComplianceDocumentTransition):
        active.complete_review(
            document_type=document_type,
            completed_on=date(2026, 10, 1),
            at=LATER,
            actor_id=active.created_by,
            expected_version=active.version,
        )


def test_start_review_only_from_active() -> None:
    approved = advance_to_approved(compliance_document_draft())

    with pytest.raises(InvalidComplianceDocumentTransition):
        _under_review(approved)


# --- supersede -----------------------------------------------------------------


def _replacement_for(
    old: ComplianceDocument, document_type, **kwargs
) -> ComplianceDocument:
    draft = compliance_document_draft(
        document_type, code=old.code, supersedes_document_id=old.id, **kwargs
    )
    return advance_to_active(draft, document_type)


@pytest.mark.parametrize("under_review", [False, True])
def test_supersede_active_or_under_review_document(under_review: bool) -> None:
    document_type = make_document_type()
    old = advance_to_active(compliance_document_draft(document_type), document_type)
    if under_review:
        old = _under_review(old)
    replacement = _replacement_for(old, document_type)

    superseded = old.supersede(
        replacement=replacement,
        at=LATER,
        actor_id=replacement.created_by,
        expected_version=old.version,
    )

    assert superseded.status is ComplianceDocumentStatus.SUPERSEDED
    assert superseded.superseded_by_document_id == replacement.id
    assert superseded.updated_by == replacement.created_by
    assert superseded.version == old.version + 1


def test_supersede_requires_replacement_linked_active_and_same_type() -> None:
    document_type = make_document_type()
    old = advance_to_active(compliance_document_draft(document_type), document_type)
    unrelated = advance_to_active(compliance_document_draft(document_type), document_type)
    pending = advance_to_approved(
        compliance_document_draft(document_type, supersedes_document_id=old.id)
    )
    other_type = make_document_type(organization_id=old.organization_id, code="other")
    wrong_type = _replacement_for(old, other_type)

    for replacement in (unrelated, pending, wrong_type):
        with pytest.raises(ComplianceDocumentValidationError):
            old.supersede(
                replacement=replacement,
                at=LATER,
                actor_id=old.created_by,
                expected_version=old.version,
            )


def test_supersede_rejects_replacement_from_another_organization() -> None:
    document_type = make_document_type()
    old = advance_to_active(compliance_document_draft(document_type), document_type)
    foreign_type = make_document_type()
    foreign = advance_to_active(
        compliance_document_draft(foreign_type, supersedes_document_id=old.id),
        foreign_type,
    ).model_copy(update={"document_type_id": old.document_type_id})

    with pytest.raises(ComplianceDocumentValidationError):
        old.supersede(
            replacement=foreign,
            at=LATER,
            actor_id=old.created_by,
            expected_version=old.version,
        )


def test_supersede_rejects_draft_document() -> None:
    document_type = make_document_type()
    old = compliance_document_draft(document_type)
    replacement = _replacement_for(old, document_type)

    with pytest.raises(InvalidComplianceDocumentTransition):
        old.supersede(
            replacement=replacement,
            at=LATER,
            actor_id=old.created_by,
            expected_version=old.version,
        )


# --- archive and restore -------------------------------------------------------


def _documents_in_archivable_states() -> list[ComplianceDocument]:
    document_type = make_document_type()
    draft = compliance_document_draft(document_type)
    approved = advance_to_approved(compliance_document_draft(document_type))
    active = advance_to_active(compliance_document_draft(document_type), document_type)
    old = advance_to_active(compliance_document_draft(document_type), document_type)
    superseded = old.supersede(
        replacement=_replacement_for(old, document_type),
        at=LATER,
        actor_id=old.created_by,
        expected_version=old.version,
    )
    return [draft, approved, active, superseded]


@pytest.mark.parametrize("index", range(4))
def test_archive_and_restore_return_to_previous_status(index: int) -> None:
    document = _documents_in_archivable_states()[index]
    previous_status = document.status

    archived = _archive(document)
    assert archived.status is ComplianceDocumentStatus.ARCHIVED
    assert archived.status_before_archive is previous_status
    assert archived.archive_reason == "Replaced by a corporate standard"

    restored = archived.restore(
        at=LATER,
        actor_id=document.created_by,
        expected_version=archived.version,
        reason="Archived by mistake",
    )
    assert restored.status is previous_status
    assert restored.status_before_archive is None
    assert restored.archive_reason is None
    assert restored.version == archived.version + 1


def test_archive_and_restore_require_reason() -> None:
    document = compliance_document_draft()

    with pytest.raises(ComplianceDocumentReasonRequired):
        document.archive(
            at=LATER, actor_id=document.created_by, expected_version=1, reason="  "
        )
    archived = _archive(document)
    with pytest.raises(ComplianceDocumentReasonRequired):
        archived.restore(
            at=LATER,
            actor_id=document.created_by,
            expected_version=archived.version,
            reason="",
        )


def test_under_review_document_cannot_be_archived() -> None:
    document_type = make_document_type()
    under_review = _under_review(
        advance_to_active(compliance_document_draft(document_type), document_type)
    )

    with pytest.raises(InvalidComplianceDocumentTransition):
        _archive(under_review)


def test_archived_document_is_terminal_until_restored() -> None:
    document_type = make_document_type()
    archived = _archive(compliance_document_draft(document_type))

    with pytest.raises(InvalidComplianceDocumentTransition):
        _archive(archived)
    with pytest.raises(InvalidComplianceDocumentTransition):
        archived.approve(
            at=LATER, actor_id=archived.created_by, expected_version=archived.version
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"status_before_archive": None},
        {"archive_reason": None},
        {"status_before_archive": ComplianceDocumentStatus.UNDER_REVIEW},
        {"status_before_archive": ComplianceDocumentStatus.ARCHIVED},
    ],
)
def test_archived_document_requires_consistent_archive_bookkeeping(
    overrides: dict[str, Any],
) -> None:
    archived = _archive(compliance_document_draft())

    with pytest.raises(ValidationError):
        ComplianceDocument.model_validate({**dict(archived), **overrides})


@pytest.mark.parametrize(
    "overrides",
    [
        {"status_before_archive": ComplianceDocumentStatus.DRAFT},
        {"archive_reason": "Stale"},
    ],
)
def test_document_outside_archive_has_no_archive_bookkeeping(
    overrides: dict[str, Any],
) -> None:
    document = compliance_document_draft()

    with pytest.raises(ValidationError):
        ComplianceDocument.model_validate({**dict(document), **overrides})


def test_restore_requires_archived_status() -> None:
    document = compliance_document_draft()

    with pytest.raises(InvalidComplianceDocumentTransition):
        document.restore(
            at=LATER, actor_id=document.created_by, expected_version=1, reason="Back"
        )


# --- optimistic concurrency ----------------------------------------------------


def test_every_mutation_checks_expected_version() -> None:
    document_type = make_document_type()
    draft = compliance_document_draft(document_type)
    approved = advance_to_approved(compliance_document_draft(document_type))
    active = advance_to_active(compliance_document_draft(document_type), document_type)
    under_review = _under_review(
        advance_to_active(compliance_document_draft(document_type), document_type)
    )
    archived = _archive(compliance_document_draft(document_type))
    actor = draft.created_by
    stale = 99

    mutations = [
        lambda: draft.update_details(at=LATER, actor_id=actor, expected_version=stale),
        lambda: draft.attach_file(
            file=make_document_file(draft),
            at=LATER,
            actor_id=actor,
            expected_version=stale,
        ),
        lambda: draft.approve(at=LATER, actor_id=actor, expected_version=stale),
        lambda: approved.activate(
            document_type=document_type,
            at=LATER,
            actor_id=actor,
            expected_version=stale,
        ),
        lambda: active.start_review(at=LATER, actor_id=actor, expected_version=stale),
        lambda: under_review.complete_review(
            document_type=document_type,
            completed_on=date(2026, 10, 1),
            at=LATER,
            actor_id=actor,
            expected_version=stale,
        ),
        lambda: active.supersede(
            replacement=_replacement_for(active, document_type),
            at=LATER,
            actor_id=actor,
            expected_version=stale,
        ),
        lambda: draft.archive(
            at=LATER, actor_id=actor, expected_version=stale, reason="x"
        ),
        lambda: archived.restore(
            at=LATER, actor_id=actor, expected_version=stale, reason="x"
        ),
    ]
    for mutate in mutations:
        with pytest.raises(ComplianceDocumentVersionConflict):
            mutate()


# --- review due (D11) ----------------------------------------------------------


def _active_with_next_review(next_review_at: date, **type_overrides):
    document_type = make_document_type(**type_overrides)
    return _active_of_type(document_type, next_review_at), document_type


def _active_of_type(document_type, next_review_at: date) -> ComplianceDocument:
    return advance_to_active(
        compliance_document_draft(document_type, next_review_at=next_review_at),
        document_type,
    )


def test_is_review_due_uses_largest_warning_threshold_inclusively() -> None:
    as_of = date(2026, 10, 1)
    document_type = make_document_type(warning_thresholds_days=(7, 90, 30))
    on_cutoff = _active_of_type(document_type, as_of + timedelta(days=90))
    beyond_cutoff = _active_of_type(document_type, as_of + timedelta(days=91))
    overdue = _active_of_type(document_type, as_of - timedelta(days=1))

    assert on_cutoff.is_review_due(as_of=as_of, document_type=document_type) is True
    assert overdue.is_review_due(as_of=as_of, document_type=document_type) is True
    assert beyond_cutoff.is_review_due(as_of=as_of, document_type=document_type) is False


def test_is_review_due_is_false_without_review_period() -> None:
    document, document_type = _active_with_next_review(
        date(2026, 1, 1), review_period_months=None
    )

    assert document.is_review_due(as_of=date(2026, 10, 1), document_type=document_type) is False


def test_is_review_due_is_false_without_next_review_at() -> None:
    document_type = make_document_type(review_period_months=None, validity_months=12)
    document_type_with_period = document_type.model_copy(
        update={"validity_months": None, "review_period_months": 60}
    )
    document = advance_to_active(compliance_document_draft(document_type), document_type)

    assert document.next_review_at is None
    assert (
        document.is_review_due(
            as_of=date(2026, 10, 1), document_type=document_type_with_period
        )
        is False
    )


def test_is_review_due_applies_only_to_active_and_under_review() -> None:
    as_of = date(2026, 10, 1)
    document, document_type = _active_with_next_review(as_of)
    under_review = _under_review(document)
    archived = _archive(document)
    superseded = document.supersede(
        replacement=_replacement_for(document, document_type),
        at=LATER,
        actor_id=document.created_by,
        expected_version=document.version,
    )
    approved = advance_to_approved(
        compliance_document_draft(document_type, next_review_at=as_of)
    )

    assert under_review.is_review_due(as_of=as_of, document_type=document_type) is True
    for document in (archived, superseded, approved):
        assert document.is_review_due(as_of=as_of, document_type=document_type) is False


def test_is_review_due_rejects_a_datetime_as_of() -> None:
    document, document_type = _active_with_next_review(date(2026, 10, 1))

    with pytest.raises(TypeError, match="date, not a datetime"):
        document.is_review_due(as_of=FIXED_AT, document_type=document_type)


def test_is_review_due_rejects_a_different_document_type() -> None:
    document, _ = _active_with_next_review(date(2026, 10, 1))

    with pytest.raises(ComplianceDocumentValidationError):
        document.is_review_due(
            as_of=date(2026, 10, 1),
            document_type=make_document_type(organization_id=document.organization_id),
        )
