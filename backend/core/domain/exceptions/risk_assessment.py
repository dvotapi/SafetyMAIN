from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.safety_ids import RiskAssessmentId


class RiskAssessmentError(SafetyMainDomainError):
    """Base error for Risk Assessment aggregate invariants."""


class RiskAssessmentNotFound(RiskAssessmentError):
    def __init__(self, risk_assessment_id: RiskAssessmentId) -> None:
        self.risk_assessment_id = risk_assessment_id
        super().__init__(
            f"Risk assessment was not found: {risk_assessment_id.value}."
        )


class DuplicateRiskAssessmentCode(RiskAssessmentError):
    def __init__(self, *, organization_id: object, code: str) -> None:
        self.organization_id = organization_id
        self.code = code
        super().__init__(
            f"Risk assessment code already exists in organization: {code}."
        )


class InvalidRiskAssessmentTransition(RiskAssessmentError):
    def __init__(
        self,
        *,
        risk_assessment_id: RiskAssessmentId,
        source: str,
        target: str,
    ) -> None:
        self.risk_assessment_id = risk_assessment_id
        self.source = source
        self.target = target
        super().__init__(
            f"Invalid risk assessment lifecycle transition: {source} -> {target}."
        )


class RiskAssessmentCannotBeModified(RiskAssessmentError):
    def __init__(self, risk_assessment_id: RiskAssessmentId, *, reason: str) -> None:
        self.risk_assessment_id = risk_assessment_id
        self.reason = reason
        super().__init__(f"Risk assessment cannot be modified: {reason}.")


class RiskAssessmentVersionConflict(RiskAssessmentError):
    def __init__(
        self,
        *,
        risk_assessment_id: RiskAssessmentId,
        expected_version: int,
        actual_version: int,
    ) -> None:
        self.risk_assessment_id = risk_assessment_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Risk assessment version conflict: "
            f"expected {expected_version}, actual {actual_version}."
        )


class RiskAssessmentHazardNotActive(RiskAssessmentError):
    def __init__(self, *, hazard_id: object) -> None:
        self.hazard_id = hazard_id
        super().__init__("Risk assessments require an active hazard.")


class RiskAssessmentInherentRiskRequired(RiskAssessmentError):
    def __init__(self) -> None:
        super().__init__("Inherent risk evaluation is required before approval.")


class RiskAssessmentAcceptanceRequired(RiskAssessmentError):
    def __init__(self) -> None:
        super().__init__("Risk acceptance decision is required before approval.")


class InvalidAssessmentProfile(RiskAssessmentError):
    def __init__(self, profile: str) -> None:
        self.profile = profile
        super().__init__(f"Invalid assessment profile: {profile}.")


class InvalidRiskEvaluation(RiskAssessmentError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class RiskAssessmentAlreadyApproved(RiskAssessmentError):
    def __init__(self, risk_assessment_id: RiskAssessmentId) -> None:
        self.risk_assessment_id = risk_assessment_id
        super().__init__(
            f"Risk assessment is already approved: {risk_assessment_id.value}."
        )


class RiskAssessmentAlreadyArchived(RiskAssessmentError):
    def __init__(self, risk_assessment_id: RiskAssessmentId) -> None:
        self.risk_assessment_id = risk_assessment_id
        super().__init__(
            f"Risk assessment is already archived: {risk_assessment_id.value}."
        )


class RiskAssessmentArchiveReasonRequired(RiskAssessmentError):
    def __init__(self) -> None:
        super().__init__("Archive reason is required.")
