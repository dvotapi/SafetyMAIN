from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.safety_ids import HazardId


class HazardError(SafetyMainDomainError):
    """Base error for Hazard aggregate invariants."""


class HazardNotFound(HazardError):
    def __init__(self, hazard_id: HazardId) -> None:
        self.hazard_id = hazard_id
        super().__init__(f"Hazard was not found: {hazard_id.value}.")


class DuplicateHazardCode(HazardError):
    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(f"Hazard code already exists in organization: {code}.")


class InvalidHazardTransition(HazardError):
    def __init__(self, *, hazard_id: HazardId, source: str, target: str) -> None:
        self.hazard_id = hazard_id
        self.source = source
        self.target = target
        super().__init__(
            f"Invalid hazard lifecycle transition: {source} -> {target}."
        )


class HazardAlreadyActive(HazardError):
    def __init__(self, hazard_id: HazardId) -> None:
        self.hazard_id = hazard_id
        super().__init__(f"Hazard is already active: {hazard_id.value}.")


class HazardAlreadyArchived(HazardError):
    def __init__(self, hazard_id: HazardId) -> None:
        self.hazard_id = hazard_id
        super().__init__(f"Hazard is already archived: {hazard_id.value}.")


class HazardNotArchived(HazardError):
    def __init__(self, hazard_id: HazardId) -> None:
        self.hazard_id = hazard_id
        super().__init__(f"Hazard is not archived: {hazard_id.value}.")


class HazardCannotBeModified(HazardError):
    def __init__(self, hazard_id: HazardId, *, reason: str) -> None:
        self.hazard_id = hazard_id
        self.reason = reason
        super().__init__(f"Hazard cannot be modified: {reason}.")


class HazardVersionConflict(HazardError):
    def __init__(
        self,
        *,
        hazard_id: HazardId,
        expected_version: int,
        actual_version: int,
    ) -> None:
        self.hazard_id = hazard_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Hazard version conflict: "
            f"expected {expected_version}, actual {actual_version}."
        )


class HazardTitleRequired(HazardError):
    def __init__(self) -> None:
        super().__init__("Hazard title is required.")


class HazardCategoryRequired(HazardError):
    def __init__(self) -> None:
        super().__init__("Hazard category is required.")


class HazardSafetyDirectionRequired(HazardError):
    def __init__(self) -> None:
        super().__init__("At least one safety direction is required.")


class InvalidHazardCategory(HazardError):
    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(f"Invalid hazard category: {category}.")


class InvalidSafetyDirection(HazardError):
    def __init__(self, direction: str) -> None:
        self.direction = direction
        super().__init__(f"Invalid safety direction: {direction}.")


class InvalidHazardSource(HazardError):
    def __init__(self, source: str) -> None:
        self.source = source
        super().__init__(f"Invalid hazard source: {source}.")


class InvalidAffectedSubject(HazardError):
    def __init__(self, subject: str) -> None:
        self.subject = subject
        super().__init__(f"Invalid affected subject: {subject}.")


class HazardArchiveReasonRequired(HazardError):
    def __init__(self) -> None:
        super().__init__("Archive reason is required.")


class HazardRestoreReasonRequired(HazardError):
    def __init__(self) -> None:
        super().__init__("Restore reason is required.")
