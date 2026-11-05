from __future__ import annotations

from enum import Enum


class SlotKeptOn(str, Enum):
    """What a shelf place is kept on («Ведётся на»)."""

    ORGANIZATION = "organization"
    FACILITY = "facility"
    EVENT = "event"
    EMPLOYEE = "employee"
    ASSET = "asset"
    PROFESSION = "profession"


class SlotObligationLevel(str, Enum):
    """«Обязательность» of a shelf place."""

    MANDATORY = "mandatory"
    CONDITIONAL = "conditional"
    RECOMMENDED = "recommended"


class CuratedSlotStatus(str, Enum):
    """Status maintained by curators when no document backs the place."""

    PRESENT = "present"
    PRESENT_NEEDS_REVIEW = "present_needs_review"
    IN_PROGRESS = "in_progress"
    MISSING = "missing"
    TO_CLARIFY = "to_clarify"


class SlotExclusionReason(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    CONDITION_NOT_MET = "condition_not_met"
    DUPLICATE = "duplicate"
    OTHER = "other"


class LegalBasisConfidence(str, Enum):
    VERIFIED = "verified"
    SECONDARY = "secondary"
    UNCONFIRMED = "unconfirmed"
    NONE = "none"


class ShelfEffectiveStatus(str, Enum):
    """Backend-computed status of a place (TASK-P11-012 §2.2)."""

    EXCLUDED = "excluded"
    PRESENT = "present"
    PRESENT_UNVERIFIED = "present_unverified"
    REVIEW_DUE = "review_due"
    OVERDUE_REVIEW = "overdue_review"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    MISSING = "missing"
    TO_CLARIFY = "to_clarify"


class ShelfStatusGroup(str, Enum):
    """Presentation group of an effective status, used for counts and colours."""

    PRESENT = "present"
    REVIEW = "review"
    IN_PROGRESS = "in_progress"
    MISSING = "missing"
    TO_CLARIFY = "to_clarify"
    EXCLUDED = "excluded"


class ShelfAction(str, Enum):
    """Action the backend offers for a place; the frontend never infers them."""

    DEVELOP_DOCUMENT = "develop_document"
    LINK_DOCUMENT = "link_document"
    EXCLUDE = "exclude"
    RESTORE = "restore"
    CONFIRM_APPLICABLE = "confirm_applicable"
    OPEN_PROJECT = "open_project"
    OPEN_DOCUMENT = "open_document"
    UPLOAD_SCAN = "upload_scan"
    START_REVIEW = "start_review"
    SEND_FOR_ACKNOWLEDGEMENT = "send_for_acknowledgement"
