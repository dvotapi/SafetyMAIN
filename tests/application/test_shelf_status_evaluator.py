from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from backend.core.application.services.shelf_status_evaluator import (
    SlotEvaluation,
    available_actions,
    evaluate,
    status_group,
    summarize,
)
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    ShelfAction,
    ShelfEffectiveStatus,
    ShelfStatusGroup,
    SlotExclusionReason,
    SlotObligationLevel,
)
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    compliance_document_draft,
    make_actor,
    make_document_type,
)
from tests.fixtures.shelf import make_section, make_slot

TODAY = date(2026, 11, 5)
S = ShelfEffectiveStatus
A = ShelfAction


def _slot(**kwargs: Any) -> ShelfSlot:
    return make_slot(make_section(), **kwargs)


def _type(slot: ShelfSlot, **kwargs: Any) -> DocumentType:
    return make_document_type(organization_id=slot.organization_id, **kwargs)


def _document(
    document_type: DocumentType,
    status: ComplianceDocumentStatus,
    *,
    effective_from: date | None = date(2025, 1, 10),
    next_review_at: date | None = None,
    updated_at: datetime = FIXED_AT,
) -> ComplianceDocument:
    return compliance_document_draft(document_type).model_copy(
        update={
            "status": status,
            "effective_from": effective_from,
            "next_review_at": next_review_at,
            "updated_at": updated_at,
        }
    )


def _linked(slot: ShelfSlot, *documents: ComplianceDocument) -> ShelfSlot:
    return slot.model_copy(update={"linked_document_ids": tuple(d.id for d in documents)})


def _evaluate(
    slot: ShelfSlot, documents: tuple[ComplianceDocument, ...], *types: DocumentType
) -> SlotEvaluation:
    return evaluate(slot, documents, {t.id: t for t in types}, TODAY)


def test_excluded_wins_over_an_active_document() -> None:
    slot = _slot()
    document_type = _type(slot)
    active = _document(document_type, ComplianceDocumentStatus.ACTIVE)
    slot = _linked(slot, active).exclude(
        reason=SlotExclusionReason.DUPLICATE,
        comment="Дубль места",
        at=FIXED_AT,
        actor_id=make_actor(),
        expected_version=1,
    )
    result = _evaluate(slot, (active,), document_type)
    assert result.effective_status is S.EXCLUDED
    assert result.group is ShelfStatusGroup.EXCLUDED
    assert result.current_document_id is None


@pytest.mark.parametrize(
    ("days_until_review", "expected"),
    [(-1, S.OVERDUE_REVIEW), (0, S.REVIEW_DUE), (90, S.REVIEW_DUE), (91, S.PRESENT)],
)
def test_active_document_review_date_from_next_review_at(
    days_until_review: int, expected: ShelfEffectiveStatus
) -> None:
    slot = _slot()
    document_type = _type(slot)
    review = TODAY + timedelta(days=days_until_review)
    active = _document(document_type, ComplianceDocumentStatus.ACTIVE, next_review_at=review)
    result = _evaluate(_linked(slot, active), (active,), document_type)
    assert result.effective_status is expected
    assert result.review_date == review
    assert result.current_document_id == active.id


def test_warning_window_is_the_largest_type_threshold() -> None:
    slot = _slot()
    document_type = _type(slot, warning_thresholds_days=(7, 30))
    near = _document(
        document_type,
        ComplianceDocumentStatus.ACTIVE,
        next_review_at=TODAY + timedelta(days=30),
    )
    far = near.model_copy(update={"next_review_at": TODAY + timedelta(days=31)})
    assert _evaluate(_linked(slot, near), (near,), document_type).effective_status is S.REVIEW_DUE
    assert _evaluate(_linked(slot, far), (far,), document_type).effective_status is S.PRESENT


def test_unknown_document_type_uses_default_window() -> None:
    slot = _slot()
    document_type = _type(slot)
    active = _document(
        document_type,
        ComplianceDocumentStatus.ACTIVE,
        next_review_at=TODAY + timedelta(days=90),
    )
    assert _evaluate(_linked(slot, active), (active,)).effective_status is S.REVIEW_DUE


def test_review_date_from_effective_from_and_type_period() -> None:
    slot = _slot(review_period_months=12)
    document_type = _type(slot, review_period_months=24)
    active = _document(
        document_type, ComplianceDocumentStatus.ACTIVE, effective_from=date(2025, 6, 10)
    )
    result = _evaluate(_linked(slot, active), (active,), document_type)
    assert result.review_date == date(2027, 6, 10)
    assert result.effective_status is S.PRESENT


def test_review_date_falls_back_to_place_period() -> None:
    slot = _slot(review_period_months=12)
    document_type = _type(slot, review_period_months=None)
    active = _document(
        document_type, ComplianceDocumentStatus.ACTIVE, effective_from=date(2025, 1, 10)
    )
    result = _evaluate(_linked(slot, active), (active,), document_type)
    assert result.review_date == date(2026, 1, 10)
    assert result.effective_status is S.OVERDUE_REVIEW


def test_no_review_rule_means_present() -> None:
    slot = _slot()
    document_type = _type(slot, review_period_months=None)
    active = _document(document_type, ComplianceDocumentStatus.ACTIVE)
    result = _evaluate(_linked(slot, active), (active,), document_type)
    assert (result.effective_status, result.review_date) == (S.PRESENT, None)


def test_under_review_wins_over_overdue() -> None:
    slot = _slot()
    document_type = _type(slot)
    document = _document(
        document_type,
        ComplianceDocumentStatus.UNDER_REVIEW,
        next_review_at=TODAY - timedelta(days=10),
    )
    assert (
        _evaluate(_linked(slot, document), (document,), document_type).effective_status
        is S.UNDER_REVIEW
    )


def test_current_edition_is_latest_effective_from() -> None:
    slot = _slot()
    document_type = _type(slot)
    older = _document(
        document_type,
        ComplianceDocumentStatus.UNDER_REVIEW,
        effective_from=date(2020, 1, 1),
    )
    newer = _document(
        document_type,
        ComplianceDocumentStatus.ACTIVE,
        effective_from=date(2025, 6, 1),
        next_review_at=TODAY + timedelta(days=400),
    )
    result = _evaluate(_linked(slot, older, newer), (older, newer), document_type)
    assert result.current_document_id == newer.id
    assert result.effective_status is S.PRESENT


def test_tie_on_effective_from_uses_latest_update() -> None:
    slot = _slot()
    document_type = _type(slot)
    first = _document(document_type, ComplianceDocumentStatus.ACTIVE, updated_at=FIXED_AT)
    second = _document(
        document_type,
        ComplianceDocumentStatus.ACTIVE,
        updated_at=FIXED_AT + timedelta(minutes=1),
    )
    result = _evaluate(_linked(slot, first, second), (first, second), document_type)
    assert result.current_document_id == second.id


@pytest.mark.parametrize(
    "status", [ComplianceDocumentStatus.DRAFT, ComplianceDocumentStatus.APPROVED]
)
def test_draft_or_approved_only_is_in_progress(status: ComplianceDocumentStatus) -> None:
    slot = _slot(curated_status=CuratedSlotStatus.MISSING)
    document_type = _type(slot)
    project = _document(document_type, status)
    result = _evaluate(_linked(slot, project), (project,), document_type)
    assert result.effective_status is S.IN_PROGRESS
    assert result.project_document_id == project.id
    assert result.current_document_id is None


def test_in_force_document_wins_over_project() -> None:
    slot = _slot()
    document_type = _type(slot)
    project = _document(document_type, ComplianceDocumentStatus.DRAFT)
    active = _document(
        document_type,
        ComplianceDocumentStatus.ACTIVE,
        next_review_at=TODAY + timedelta(days=400),
    )
    result = _evaluate(_linked(slot, project, active), (project, active), document_type)
    assert result.effective_status is S.PRESENT
    assert result.project_document_id == project.id


@pytest.mark.parametrize(
    ("curated", "expected"),
    [
        (CuratedSlotStatus.PRESENT, S.PRESENT_UNVERIFIED),
        (CuratedSlotStatus.PRESENT_NEEDS_REVIEW, S.REVIEW_DUE),
        (CuratedSlotStatus.IN_PROGRESS, S.IN_PROGRESS),
        (CuratedSlotStatus.MISSING, S.MISSING),
        (CuratedSlotStatus.TO_CLARIFY, S.TO_CLARIFY),
    ],
)
def test_curated_fallback(curated: CuratedSlotStatus, expected: ShelfEffectiveStatus) -> None:
    slot = _slot(curated_status=curated)
    document_type = _type(slot)
    superseded = _document(document_type, ComplianceDocumentStatus.SUPERSEDED)
    archived = _document(document_type, ComplianceDocumentStatus.ARCHIVED)
    result = _evaluate(_linked(slot, superseded, archived), (superseded, archived), document_type)
    assert result.effective_status is expected
    assert result.current_document_id is None


def test_documents_not_linked_to_the_place_are_ignored() -> None:
    slot = _slot(curated_status=CuratedSlotStatus.MISSING)
    document_type = _type(slot)
    stranger = _document(document_type, ComplianceDocumentStatus.ACTIVE)
    assert _evaluate(slot, (stranger,), document_type).effective_status is S.MISSING


def test_today_must_be_a_date() -> None:
    with pytest.raises(TypeError):
        evaluate(_slot(), (), {}, datetime(2026, 11, 5, tzinfo=UTC))


@pytest.mark.parametrize(
    ("status", "group"),
    [
        (S.PRESENT, ShelfStatusGroup.PRESENT),
        (S.PRESENT_UNVERIFIED, ShelfStatusGroup.PRESENT),
        (S.REVIEW_DUE, ShelfStatusGroup.REVIEW),
        (S.OVERDUE_REVIEW, ShelfStatusGroup.REVIEW),
        (S.UNDER_REVIEW, ShelfStatusGroup.REVIEW),
        (S.IN_PROGRESS, ShelfStatusGroup.IN_PROGRESS),
        (S.MISSING, ShelfStatusGroup.MISSING),
        (S.TO_CLARIFY, ShelfStatusGroup.TO_CLARIFY),
        (S.EXCLUDED, ShelfStatusGroup.EXCLUDED),
    ],
)
def test_presentation_groups(status: ShelfEffectiveStatus, group: ShelfStatusGroup) -> None:
    assert status_group(status) is group


def _with_docs(status: ShelfEffectiveStatus) -> SlotEvaluation:
    from uuid import uuid4

    from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId

    document_id = ComplianceDocumentId(value=uuid4())
    return SlotEvaluation(
        effective_status=status,
        group=status_group(status),
        review_date=None,
        current_document_id=document_id,
        project_document_id=document_id,
    )


@pytest.mark.parametrize(
    ("status", "primary", "others"),
    [
        (S.MISSING, A.DEVELOP_DOCUMENT, (A.LINK_DOCUMENT, A.EXCLUDE)),
        (S.TO_CLARIFY, A.CONFIRM_APPLICABLE, (A.EXCLUDE,)),
        (S.IN_PROGRESS, A.OPEN_PROJECT, (A.LINK_DOCUMENT, A.EXCLUDE)),
        (S.PRESENT_UNVERIFIED, A.UPLOAD_SCAN, (A.LINK_DOCUMENT, A.EXCLUDE)),
        (S.PRESENT, A.OPEN_DOCUMENT, (A.EXCLUDE,)),
        (S.REVIEW_DUE, A.START_REVIEW, (A.EXCLUDE,)),
        (S.OVERDUE_REVIEW, A.START_REVIEW, (A.EXCLUDE,)),
        (S.UNDER_REVIEW, A.OPEN_DOCUMENT, (A.EXCLUDE,)),
        (S.EXCLUDED, A.RESTORE, ()),
    ],
)
def test_curator_actions_table(
    status: ShelfEffectiveStatus, primary: ShelfAction, others: tuple[ShelfAction, ...]
) -> None:
    actions = available_actions(_with_docs(status), can_curate=True, can_create_document=True)
    assert (actions.primary, actions.others) == (primary, others)
    assert actions.all == (primary, *others)


def test_curator_without_document_create_cannot_develop() -> None:
    actions = available_actions(
        _with_docs(S.MISSING), can_curate=True, can_create_document=False
    )
    assert (actions.primary, actions.others) == (None, (A.LINK_DOCUMENT, A.EXCLUDE))


def test_document_actions_need_an_existing_document() -> None:
    curated_review = _slot(curated_status=CuratedSlotStatus.PRESENT_NEEDS_REVIEW)
    evaluation = evaluate(curated_review, (), {}, TODAY)
    actions = available_actions(evaluation, can_curate=True, can_create_document=True)
    assert (actions.primary, actions.others) == (None, (A.EXCLUDE,))
    curated_progress = _slot(curated_status=CuratedSlotStatus.IN_PROGRESS)
    evaluation = evaluate(curated_progress, (), {}, TODAY)
    actions = available_actions(evaluation, can_curate=True, can_create_document=True)
    assert (actions.primary, actions.others) == (None, (A.LINK_DOCUMENT, A.EXCLUDE))


@pytest.mark.parametrize(
    ("status", "primary"),
    [
        (S.PRESENT, A.OPEN_DOCUMENT),
        (S.REVIEW_DUE, A.OPEN_DOCUMENT),
        (S.UNDER_REVIEW, A.OPEN_DOCUMENT),
        (S.IN_PROGRESS, A.OPEN_PROJECT),
        (S.EXCLUDED, None),
    ],
)
def test_viewer_only_opens_documents(
    status: ShelfEffectiveStatus, primary: ShelfAction | None
) -> None:
    actions = available_actions(_with_docs(status), can_curate=False, can_create_document=True)
    assert (actions.primary, actions.others) == (primary, ())


@pytest.mark.parametrize(
    "curated", [CuratedSlotStatus.MISSING, CuratedSlotStatus.PRESENT, CuratedSlotStatus.TO_CLARIFY]
)
def test_viewer_without_documents_gets_no_actions(curated: CuratedSlotStatus) -> None:
    evaluation = evaluate(_slot(curated_status=curated), (), {}, TODAY)
    actions = available_actions(evaluation, can_curate=False, can_create_document=False)
    assert actions.all == ()


def test_summary_counts_and_readiness() -> None:
    mandatory = _slot(obligation_level=SlotObligationLevel.MANDATORY)
    recommended = _slot(obligation_level=SlotObligationLevel.RECOMMENDED)
    statuses = [
        (mandatory, S.PRESENT),
        (mandatory, S.PRESENT_UNVERIFIED),
        (recommended, S.EXCLUDED),
        (mandatory, S.MISSING),
        (recommended, S.TO_CLARIFY),
        (mandatory, S.REVIEW_DUE),
        (mandatory, S.IN_PROGRESS),
        (mandatory, S.OVERDUE_REVIEW),
    ]
    summary = summarize(statuses)
    assert summary.total == 8
    assert summary.mandatory_total == 6
    assert dict(summary.by_group) == {
        ShelfStatusGroup.PRESENT: 2,
        ShelfStatusGroup.REVIEW: 2,
        ShelfStatusGroup.IN_PROGRESS: 1,
        ShelfStatusGroup.MISSING: 1,
        ShelfStatusGroup.TO_CLARIFY: 1,
        ShelfStatusGroup.EXCLUDED: 1,
    }
    # (2 present + 1 excluded) / 8 = 37.5 % → 38 (half up)
    assert summary.readiness_percent == 38


@pytest.mark.parametrize(
    ("ready", "total", "percent"), [(0, 0, 0), (1, 3, 33), (2, 3, 67), (1, 8, 13), (3, 3, 100)]
)
def test_readiness_rounding(ready: int, total: int, percent: int) -> None:
    slot = _slot()
    statuses = [(slot, S.PRESENT)] * ready + [(slot, S.MISSING)] * (total - ready)
    assert summarize(statuses).readiness_percent == percent


@pytest.mark.parametrize("status", [S.PRESENT, S.REVIEW_DUE, S.OVERDUE_REVIEW, S.UNDER_REVIEW])
def test_upload_signed_scan_is_offered_while_the_current_document_has_none(
    status: ShelfEffectiveStatus,
) -> None:
    evaluation = _with_docs(status)

    actions = available_actions(
        evaluation, can_curate=True, can_create_document=True, can_update_document=True
    )

    assert actions.others == (A.UPLOAD_SIGNED_SCAN, A.EXCLUDE)


def test_upload_signed_scan_is_hidden_when_scanned_or_not_permitted() -> None:
    from dataclasses import replace

    scanned = replace(_with_docs(S.PRESENT), current_has_signed_scan=True)
    for evaluation, can_update in (
        (scanned, True),
        (_with_docs(S.PRESENT), False),
        (_with_docs(S.MISSING), True),
        (_with_docs(S.IN_PROGRESS), True),
    ):
        actions = available_actions(
            evaluation, can_curate=True, can_create_document=True, can_update_document=can_update
        )
        assert A.UPLOAD_SIGNED_SCAN not in actions.all
    viewer = available_actions(
        _with_docs(S.PRESENT), can_curate=False, can_create_document=True, can_update_document=True
    )
    assert viewer.all == (A.OPEN_DOCUMENT,)


def test_evaluation_records_whether_the_current_document_has_a_signed_scan() -> None:
    from backend.core.domain.value_objects.compliance_enums import DocumentFileRole
    from tests.fixtures.compliance_documents import (
        advance_to_active,
        make_document_file,
    )

    slot = _slot()
    document_type = _type(slot)
    active = advance_to_active(compliance_document_draft(document_type), document_type)
    scan = make_document_file(active, filename="s.pdf").model_copy(
        update={"role": DocumentFileRole.SIGNED_SCAN}
    )
    scanned = active.attach_signed_scan(
        file=scan, at=active.updated_at, actor_id=active.created_by, expected_version=active.version
    )
    slot = _linked(slot, active)

    assert evaluate(slot, [active], {document_type.id: document_type}, TODAY).current_has_signed_scan is False
    assert evaluate(slot, [scanned], {document_type.id: document_type}, TODAY).current_has_signed_scan is True
