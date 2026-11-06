"""Which places the scan attachment script may fill (TASK-P11-012 §4.5, plan S2–S3, S6).

No file or storage access here. The caller passes ``locate``, which resolves a
place's ``legacy_location`` to a PDF under the chosen root (or explains why it
cannot).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects.shelf_enums import CuratedSlotStatus


class SkipReason(str, Enum):
    NOT_PRESENT = "not_present"
    EXCLUDED = "excluded"
    HAS_DOCUMENT = "has_document"
    NO_DOCUMENT_TYPE = "no_document_type"
    TYPE_NOT_FOUND = "type_not_found"
    TYPE_REQUIRES_APPROVAL_ORDER = "type_requires_approval_order"
    NO_LOCATION = "no_location"
    FILE_NOT_FOUND = "file_not_found"
    AMBIGUOUS = "ambiguous"
    NOT_PDF = "not_pdf"
    OUTSIDE_ROOT = "outside_root"
    TOO_LARGE = "too_large"


@dataclass(frozen=True, slots=True)
class LocatedFile:
    path: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class LocateResult:
    file: LocatedFile | None = None
    reason: SkipReason | None = None


@dataclass(frozen=True, slots=True)
class AttachCandidate:
    slot: ShelfSlot
    document_type: DocumentType
    file: LocatedFile


@dataclass(frozen=True, slots=True)
class SkippedPlace:
    code: str
    reason: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class AttachmentPlan:
    candidates: tuple[AttachCandidate, ...]
    skipped: tuple[SkippedPlace, ...]


def plan_attachments(
    slots: Iterable[ShelfSlot],
    active_types: Mapping[str, DocumentType],
    locate: Callable[[str], LocateResult],
) -> AttachmentPlan:
    """Rules in the order of TASK §4.5; the first failing rule is the reason."""
    candidates: list[AttachCandidate] = []
    skipped: list[SkippedPlace] = []
    for slot in sorted(slots, key=lambda item: item.code.sort_key):
        reason, document_type, file = _decide(slot, active_types, locate)
        if reason is not None:
            skipped.append(SkippedPlace(code=slot.code.value, reason=reason.value))
            continue
        assert document_type is not None and file is not None
        candidates.append(AttachCandidate(slot=slot, document_type=document_type, file=file))
    return AttachmentPlan(candidates=tuple(candidates), skipped=tuple(skipped))


def _decide(
    slot: ShelfSlot,
    active_types: Mapping[str, DocumentType],
    locate: Callable[[str], LocateResult],
) -> tuple[SkipReason | None, DocumentType | None, LocatedFile | None]:
    if slot.is_excluded:
        return SkipReason.EXCLUDED, None, None
    if slot.curated_status is not CuratedSlotStatus.PRESENT:
        return SkipReason.NOT_PRESENT, None, None
    if slot.linked_document_ids:
        return SkipReason.HAS_DOCUMENT, None, None
    if not slot.document_type_code:
        return SkipReason.NO_DOCUMENT_TYPE, None, None
    document_type = active_types.get(slot.document_type_code)
    if document_type is None:
        return SkipReason.TYPE_NOT_FOUND, None, None
    if document_type.requires_approval_order:
        return SkipReason.TYPE_REQUIRES_APPROVAL_ORDER, None, None
    if not slot.legacy_location.strip():
        return SkipReason.NO_LOCATION, None, None
    located = locate(slot.legacy_location)
    if located.file is None:
        return located.reason or SkipReason.FILE_NOT_FOUND, None, None
    return None, document_type, located.file
