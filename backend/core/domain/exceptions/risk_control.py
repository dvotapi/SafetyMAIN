from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.safety_ids import RiskControlId


class RiskControlError(SafetyMainDomainError):
    """Base error for RiskControl aggregate invariants."""


class RiskControlNotFound(RiskControlError):
    def __init__(self, control_id: RiskControlId) -> None:
        self.control_id = control_id
        super().__init__(f"Risk control was not found: {control_id.value}.")


class DuplicateRiskControlCode(RiskControlError):
    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(f"Risk control code already exists in organization: {code}.")


class InvalidRiskControlTransition(RiskControlError):
    def __init__(self, *, control_id: RiskControlId, source: str, target: str) -> None:
        self.control_id = control_id
        self.source = source
        self.target = target
        super().__init__(
            f"Invalid risk control lifecycle transition: {source} -> {target}."
        )


class RiskControlValidationError(RiskControlError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class RiskControlVersionConflict(RiskControlError):
    def __init__(
        self,
        *,
        control_id: RiskControlId,
        expected_version: int,
        actual_version: int,
    ) -> None:
        self.control_id = control_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Risk control version conflict: "
            f"expected {expected_version}, actual {actual_version}."
        )


class RiskControlCannotBeModified(RiskControlError):
    def __init__(self, control_id: RiskControlId, *, reason: str) -> None:
        self.control_id = control_id
        self.reason = reason
        super().__init__(f"Risk control cannot be modified: {reason}.")


class RiskControlAlreadyMaterialized(RiskControlError):
    def __init__(self, *, source_control_reference: str) -> None:
        self.source_control_reference = source_control_reference
        super().__init__(
            "Risk control already materialized for source reference: "
            f"{source_control_reference}."
        )


class RiskControlReasonRequired(RiskControlError):
    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"{action} reason is required.")
