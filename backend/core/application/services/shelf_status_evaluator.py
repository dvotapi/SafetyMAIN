"""Backend-authoritative effective status of shelf places (TASK-P11-012 §2.2).

Pure functions: handlers load the place, its linked documents and their types,
and pass ``today`` as the UTC date of ``ClockContract.now()``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.services.calendar_months import add_months
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    ShelfAction,
    ShelfEffectiveStatus,
    ShelfStatusGroup,
    SlotObligationLevel,
)

DEFAULT_REVIEW_WARNING_DAYS = 90

_IN_FORCE = frozenset(
    {ComplianceDocumentStatus.ACTIVE, ComplianceDocumentStatus.UNDER_REVIEW}
)
_IN_PROGRESS = frozenset(
    {ComplianceDocumentStatus.DRAFT, ComplianceDocumentStatus.APPROVED}
)

_CURATED_FALLBACK: dict[CuratedSlotStatus, ShelfEffectiveStatus] = {
    CuratedSlotStatus.PRESENT: ShelfEffectiveStatus.PRESENT_UNVERIFIED,
    CuratedSlotStatus.PRESENT_NEEDS_REVIEW: ShelfEffectiveStatus.REVIEW_DUE,
    CuratedSlotStatus.IN_PROGRESS: ShelfEffectiveStatus.IN_PROGRESS,
    CuratedSlotStatus.MISSING: ShelfEffectiveStatus.MISSING,
    CuratedSlotStatus.TO_CLARIFY: ShelfEffectiveStatus.TO_CLARIFY,
}

_GROUPS: dict[ShelfEffectiveStatus, ShelfStatusGroup] = {
    ShelfEffectiveStatus.PRESENT: ShelfStatusGroup.PRESENT,
    ShelfEffectiveStatus.PRESENT_UNVERIFIED: ShelfStatusGroup.PRESENT,
    ShelfEffectiveStatus.REVIEW_DUE: ShelfStatusGroup.REVIEW,
    ShelfEffectiveStatus.OVERDUE_REVIEW: ShelfStatusGroup.REVIEW,
    ShelfEffectiveStatus.UNDER_REVIEW: ShelfStatusGroup.REVIEW,
    ShelfEffectiveStatus.IN_PROGRESS: ShelfStatusGroup.IN_PROGRESS,
    ShelfEffectiveStatus.MISSING: ShelfStatusGroup.MISSING,
    ShelfEffectiveStatus.TO_CLARIFY: ShelfStatusGroup.TO_CLARIFY,
    ShelfEffectiveStatus.EXCLUDED: ShelfStatusGroup.EXCLUDED,
}

# Curator actions per effective status: (primary, others) — TASK-P11-012 §2.2.
# `send_for_acknowledgement` replaces `open_document` for `present` in phase 5.
_CURATOR_ACTIONS: dict[ShelfEffectiveStatus, tuple[ShelfAction | None, tuple[ShelfAction, ...]]] = {
    ShelfEffectiveStatus.MISSING: (
        ShelfAction.DEVELOP_DOCUMENT,
        (ShelfAction.LINK_DOCUMENT, ShelfAction.EXCLUDE),
    ),
    ShelfEffectiveStatus.TO_CLARIFY: (
        ShelfAction.CONFIRM_APPLICABLE,
        (ShelfAction.EXCLUDE,),
    ),
    ShelfEffectiveStatus.IN_PROGRESS: (
        ShelfAction.OPEN_PROJECT,
        (ShelfAction.LINK_DOCUMENT, ShelfAction.EXCLUDE),
    ),
    ShelfEffectiveStatus.PRESENT_UNVERIFIED: (
        ShelfAction.UPLOAD_SCAN,
        (ShelfAction.LINK_DOCUMENT, ShelfAction.EXCLUDE),
    ),
    ShelfEffectiveStatus.PRESENT: (ShelfAction.OPEN_DOCUMENT, (ShelfAction.EXCLUDE,)),
    ShelfEffectiveStatus.REVIEW_DUE: (ShelfAction.START_REVIEW, (ShelfAction.EXCLUDE,)),
    ShelfEffectiveStatus.OVERDUE_REVIEW: (
        ShelfAction.START_REVIEW,
        (ShelfAction.EXCLUDE,),
    ),
    ShelfEffectiveStatus.UNDER_REVIEW: (
        ShelfAction.OPEN_DOCUMENT,
        (ShelfAction.EXCLUDE,),
    ),
    ShelfEffectiveStatus.EXCLUDED: (ShelfAction.RESTORE, ()),
}

# Actions that act on an existing document; dropped when the place has none.
_NEEDS_CURRENT_DOCUMENT = frozenset({ShelfAction.OPEN_DOCUMENT, ShelfAction.START_REVIEW})
_NEEDS_PROJECT_DOCUMENT = frozenset({ShelfAction.OPEN_PROJECT})


@dataclass(frozen=True, slots=True)
class SlotEvaluation:
    effective_status: ShelfEffectiveStatus
    group: ShelfStatusGroup
    review_date: date | None
    current_document_id: ComplianceDocumentId | None
    project_document_id: ComplianceDocumentId | None


@dataclass(frozen=True, slots=True)
class SlotActions:
    primary: ShelfAction | None
    others: tuple[ShelfAction, ...]

    @property
    def all(self) -> tuple[ShelfAction, ...]:
        return ((self.primary,) if self.primary else ()) + self.others


@dataclass(frozen=True, slots=True)
class ShelfSummary:
    total: int
    mandatory_total: int
    by_group: Mapping[ShelfStatusGroup, int]
    readiness_percent: int


def status_group(status: ShelfEffectiveStatus) -> ShelfStatusGroup:
    return _GROUPS[status]


def evaluate(
    slot: ShelfSlot,
    documents: Iterable[ComplianceDocument],
    document_types: Mapping[DocumentTypeId, DocumentType],
    today: date,
) -> SlotEvaluation:
    """First matching rule of §2.2 wins. ``documents`` may contain unrelated ones."""
    if isinstance(today, datetime):
        raise TypeError("today must be a date, not a datetime.")
    linked = [document for document in documents if document.id in slot.linked_document_ids]
    project = _latest(document for document in linked if document.status in _IN_PROGRESS)
    project_id = project.id if project else None

    if slot.is_excluded:
        return _evaluation(ShelfEffectiveStatus.EXCLUDED, None, None, project_id)

    current = _latest(document for document in linked if document.status in _IN_FORCE)
    if current is not None:
        document_type = document_types.get(current.document_type_id)
        review_date = _review_date(current, document_type, slot)
        status = _in_force_status(current, document_type, review_date, today)
        return _evaluation(status, review_date, current.id, project_id)

    if project is not None:
        return _evaluation(ShelfEffectiveStatus.IN_PROGRESS, None, None, project_id)

    return _evaluation(_CURATED_FALLBACK[slot.curated_status], None, None, None)


def available_actions(
    evaluation: SlotEvaluation, *, can_curate: bool, can_create_document: bool
) -> SlotActions:
    """Actions offered to the current user; viewers only open existing documents."""
    if not can_curate:
        if evaluation.effective_status is ShelfEffectiveStatus.IN_PROGRESS:
            return SlotActions(
                ShelfAction.OPEN_PROJECT if evaluation.project_document_id else None, ()
            )
        if evaluation.group is ShelfStatusGroup.EXCLUDED or not evaluation.current_document_id:
            return SlotActions(None, ())
        return SlotActions(ShelfAction.OPEN_DOCUMENT, ())

    primary, others = _CURATOR_ACTIONS[evaluation.effective_status]
    offered = [
        action
        for action in ((primary,) if primary else ()) + others
        if _possible(action, evaluation, can_create_document=can_create_document)
    ]
    if primary is not None and primary in offered:
        return SlotActions(primary, tuple(action for action in offered if action is not primary))
    return SlotActions(None, tuple(offered))


def summarize(statuses: Iterable[tuple[ShelfSlot, ShelfEffectiveStatus]]) -> ShelfSummary:
    """Counts by group and readiness `(present + excluded) / total` (D12)."""
    by_group = {group: 0 for group in ShelfStatusGroup}
    total = 0
    mandatory_total = 0
    for slot, status in statuses:
        total += 1
        by_group[_GROUPS[status]] += 1
        if slot.obligation_level is SlotObligationLevel.MANDATORY:
            mandatory_total += 1
    ready = by_group[ShelfStatusGroup.PRESENT] + by_group[ShelfStatusGroup.EXCLUDED]
    return ShelfSummary(
        total=total,
        mandatory_total=mandatory_total,
        by_group=by_group,
        readiness_percent=_percent(ready, total),
    )


def _percent(part: int, total: int) -> int:
    """Integer percent rounded half up; 0 for an empty shelf."""
    if total == 0:
        return 0
    return (200 * part + total) // (2 * total)


def _evaluation(
    status: ShelfEffectiveStatus,
    review_date: date | None,
    current_id: ComplianceDocumentId | None,
    project_id: ComplianceDocumentId | None,
) -> SlotEvaluation:
    return SlotEvaluation(
        effective_status=status,
        group=_GROUPS[status],
        review_date=review_date,
        current_document_id=current_id,
        project_document_id=project_id,
    )


def _latest(documents: Iterable[ComplianceDocument]) -> ComplianceDocument | None:
    """Most recent edition: latest `effective_from` (unset first), then `updated_at`."""
    candidates = list(documents)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda document: (document.effective_from or date.min, document.updated_at),
    )


def _review_date(
    document: ComplianceDocument,
    document_type: DocumentType | None,
    slot: ShelfSlot,
) -> date | None:
    if document.next_review_at is not None:
        return document.next_review_at
    if document.effective_from is None:
        return None
    months = (
        document_type.review_period_months
        if document_type is not None and document_type.review_period_months
        else slot.review_period_months
    )
    if months is None:
        return None
    return add_months(document.effective_from, months)


def _in_force_status(
    document: ComplianceDocument,
    document_type: DocumentType | None,
    review_date: date | None,
    today: date,
) -> ShelfEffectiveStatus:
    if document.status is ComplianceDocumentStatus.UNDER_REVIEW:
        return ShelfEffectiveStatus.UNDER_REVIEW
    if review_date is None:
        return ShelfEffectiveStatus.PRESENT
    if review_date < today:
        return ShelfEffectiveStatus.OVERDUE_REVIEW
    warning_days = (
        max(document_type.warning_thresholds_days)
        if document_type is not None
        else DEFAULT_REVIEW_WARNING_DAYS
    )
    if (review_date - today).days <= warning_days:
        return ShelfEffectiveStatus.REVIEW_DUE
    return ShelfEffectiveStatus.PRESENT


def _possible(
    action: ShelfAction, evaluation: SlotEvaluation, *, can_create_document: bool
) -> bool:
    if action in _NEEDS_CURRENT_DOCUMENT:
        return evaluation.current_document_id is not None
    if action in _NEEDS_PROJECT_DOCUMENT:
        return evaluation.project_document_id is not None
    if action is ShelfAction.DEVELOP_DOCUMENT:
        return can_create_document
    return True
