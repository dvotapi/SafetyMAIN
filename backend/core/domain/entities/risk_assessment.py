from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.exceptions.risk_assessment import (
    InvalidAssessmentProfile,
    InvalidRiskAssessmentTransition,
    InvalidRiskEvaluation,
    RiskAssessmentAcceptanceRequired,
    RiskAssessmentAlreadyApproved,
    RiskAssessmentAlreadyArchived,
    RiskAssessmentArchiveReasonRequired,
    RiskAssessmentCannotBeModified,
    RiskAssessmentInherentRiskRequired,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.services.assessment_profiles import (
    get_assessment_profile,
    resolve_matrix_level,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
    ControlMeasure,
    ReviewSchedule,
    RiskAcceptance,
    RiskEvaluation,
    RiskFactorScore,
    competency_values,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessmentProfileCode,
    CompetencyReferenceCode,
    Probability,
    RiskAcceptanceDecision,
    RiskAssessmentStatus,
    RiskFactorCode,
    RiskLevel,
    Severity,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId

_TRANSITIONS: dict[str, frozenset[str]] = {
    RiskAssessmentStatus.DRAFT.value: frozenset(
        {
            RiskAssessmentStatus.UNDER_REVIEW.value,
            RiskAssessmentStatus.APPROVED.value,
            RiskAssessmentStatus.ARCHIVED.value,
        }
    ),
    RiskAssessmentStatus.UNDER_REVIEW.value: frozenset(
        {
            RiskAssessmentStatus.APPROVED.value,
            RiskAssessmentStatus.DRAFT.value,
            RiskAssessmentStatus.ARCHIVED.value,
        }
    ),
    RiskAssessmentStatus.APPROVED.value: frozenset(
        {
            RiskAssessmentStatus.SUPERSEDED.value,
            RiskAssessmentStatus.ARCHIVED.value,
        }
    ),
    RiskAssessmentStatus.SUPERSEDED.value: frozenset(
        {RiskAssessmentStatus.ARCHIVED.value}
    ),
    RiskAssessmentStatus.ARCHIVED.value: frozenset(),
}


class RiskAssessment(BaseModel):
    """Organization-scoped risk assessment aggregate root."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: RiskAssessmentId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    hazard_id: HazardId = Field(frozen=True)
    code: RiskAssessmentCode
    title: str
    assessment_profile: AssessmentProfileCode
    assessed_object: AssessedObjectRef
    assessor_id: UserId
    assessment_date: datetime
    review_schedule: ReviewSchedule = Field(default_factory=ReviewSchedule)
    inherent_risk: RiskEvaluation | None = None
    residual_risk: RiskEvaluation | None = None
    controls: tuple[ControlMeasure, ...] = ()
    acceptance: RiskAcceptance | None = None
    competency_requirements: tuple[CompetencyReferenceCode, ...] = ()
    extension_references: dict[str, str] = Field(default_factory=dict)
    status: RiskAssessmentStatus = RiskAssessmentStatus.DRAFT
    superseded_by_id: RiskAssessmentId | None = None
    archived_at: datetime | None = None
    archived_by: UserId | None = None
    approved_at: datetime | None = None
    approved_by: UserId | None = None
    created_at: datetime = Field(frozen=True)
    updated_at: datetime
    version: int = 1

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Risk assessment title is required.")
        return normalized

    @field_validator("version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Risk assessment version must be positive.")
        return value

    @field_validator("competency_requirements")
    @classmethod
    def normalize_competencies(
        cls, value: tuple[CompetencyReferenceCode, ...]
    ) -> tuple[CompetencyReferenceCode, ...]:
        return competency_values(value)

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        hazard_id: HazardId,
        code: RiskAssessmentCode | str,
        title: str,
        assessment_profile: AssessmentProfileCode,
        assessed_object: AssessedObjectRef,
        assessor_id: UserId,
        assessment_date: datetime,
        review_schedule: ReviewSchedule | None = None,
        competency_requirements: tuple[CompetencyReferenceCode, ...] = (),
        extension_references: dict[str, str] | None = None,
        created_at: datetime | None = None,
        risk_assessment_id: RiskAssessmentId | None = None,
    ) -> RiskAssessment:
        try:
            profile = get_assessment_profile(assessment_profile)
        except ValueError as exc:
            raise InvalidAssessmentProfile(assessment_profile.value) from exc
        stamp = created_at or assessment_date
        schedule = review_schedule or ReviewSchedule(
            review_due_date=assessment_date
            + timedelta(days=profile.default_review_frequency_days),
            review_frequency_days=profile.default_review_frequency_days,
            review_reason="Initial assessment schedule",
        )
        return cls(
            id=risk_assessment_id or RiskAssessmentId(value=uuid4()),
            organization_id=organization_id,
            hazard_id=hazard_id,
            code=(
                RiskAssessmentCode(value=code)
                if isinstance(code, str)
                else code
            ),
            title=title,
            assessment_profile=assessment_profile,
            assessed_object=assessed_object,
            assessor_id=assessor_id,
            assessment_date=assessment_date,
            review_schedule=schedule,
            competency_requirements=competency_requirements,
            extension_references=dict(extension_references or {}),
            status=RiskAssessmentStatus.DRAFT,
            created_at=stamp,
            updated_at=stamp,
            version=1,
        )

    def update_details(
        self,
        *,
        at: datetime,
        expected_version: int,
        title: str | None = None,
        assessed_object: AssessedObjectRef | None = None,
        assessment_date: datetime | None = None,
        review_schedule: ReviewSchedule | None = None,
        competency_requirements: tuple[CompetencyReferenceCode, ...] | None = None,
        extension_references: dict[str, str] | None = None,
        controls: tuple[ControlMeasure, ...] | None = None,
        inherent_risk: RiskEvaluation | None = None,
        residual_risk: RiskEvaluation | None = None,
        acceptance: RiskAcceptance | None = None,
    ) -> RiskAssessment:
        self._assert_editable()
        self._assert_version(expected_version)
        updates: dict[str, Any] = {
            "updated_at": at,
            "version": self.version + 1,
        }
        if title is not None:
            updates["title"] = title
        if assessed_object is not None:
            updates["assessed_object"] = assessed_object
        if assessment_date is not None:
            updates["assessment_date"] = assessment_date
        if review_schedule is not None:
            updates["review_schedule"] = review_schedule
        if competency_requirements is not None:
            updates["competency_requirements"] = competency_requirements
        if extension_references is not None:
            updates["extension_references"] = dict(extension_references)
        if controls is not None:
            updates["controls"] = controls
        if inherent_risk is not None:
            updates["inherent_risk"] = self._validated_evaluation(inherent_risk)
        if residual_risk is not None:
            if self.inherent_risk is None and inherent_risk is None:
                raise RiskAssessmentInherentRiskRequired()
            updates["residual_risk"] = self._validated_evaluation(residual_risk)
        if acceptance is not None:
            updates["acceptance"] = acceptance
        return self.model_copy(update=updates)

    def submit_for_review(self, *, at: datetime, expected_version: int) -> RiskAssessment:
        self._assert_editable()
        self._assert_version(expected_version)
        self._assert_transition(RiskAssessmentStatus.UNDER_REVIEW)
        if self.inherent_risk is None:
            raise RiskAssessmentInherentRiskRequired()
        return self.model_copy(
            update={
                "status": RiskAssessmentStatus.UNDER_REVIEW,
                "updated_at": at,
                "version": self.version + 1,
            }
        )

    def approve(
        self,
        *,
        at: datetime,
        approved_by: UserId,
        expected_version: int,
        acceptance: RiskAcceptance | None = None,
    ) -> RiskAssessment:
        if self.status is RiskAssessmentStatus.APPROVED:
            raise RiskAssessmentAlreadyApproved(self.id)
        self._assert_version(expected_version)
        if self.status is RiskAssessmentStatus.DRAFT or self.status is RiskAssessmentStatus.UNDER_REVIEW:
            self._assert_transition(RiskAssessmentStatus.APPROVED)
        else:
            raise InvalidRiskAssessmentTransition(
                risk_assessment_id=self.id,
                source=self.status.value,
                target=RiskAssessmentStatus.APPROVED.value,
            )
        if self.inherent_risk is None:
            raise RiskAssessmentInherentRiskRequired()
        final_acceptance = acceptance or self.acceptance
        if final_acceptance is None:
            raise RiskAssessmentAcceptanceRequired()
        if (
            final_acceptance.decision
            in {
                RiskAcceptanceDecision.ACCEPTED,
                RiskAcceptanceDecision.CONDITIONALLY_ACCEPTED,
            }
            and not final_acceptance.justification
        ):
            raise InvalidRiskEvaluation(
                "Acceptance justification is required for accepted risks."
            )
        residual = self.residual_risk or self.inherent_risk
        return self.model_copy(
            update={
                "status": RiskAssessmentStatus.APPROVED,
                "acceptance": final_acceptance.model_copy(
                    update={
                        "reviewer_id": final_acceptance.reviewer_id or approved_by,
                        "approved_at": final_acceptance.approved_at or at,
                    }
                ),
                "residual_risk": residual,
                "approved_at": at,
                "approved_by": approved_by,
                "updated_at": at,
                "version": self.version + 1,
            }
        )

    def supersede(
        self,
        *,
        at: datetime,
        superseded_by_id: RiskAssessmentId,
        expected_version: int,
    ) -> RiskAssessment:
        self._assert_version(expected_version)
        if self.status is not RiskAssessmentStatus.APPROVED:
            raise InvalidRiskAssessmentTransition(
                risk_assessment_id=self.id,
                source=self.status.value,
                target=RiskAssessmentStatus.SUPERSEDED.value,
            )
        self._assert_transition(RiskAssessmentStatus.SUPERSEDED)
        return self.model_copy(
            update={
                "status": RiskAssessmentStatus.SUPERSEDED,
                "superseded_by_id": superseded_by_id,
                "updated_at": at,
                "version": self.version + 1,
            }
        )

    def archive(
        self,
        *,
        at: datetime,
        archived_by: UserId,
        reason: str,
        expected_version: int,
    ) -> RiskAssessment:
        if not reason.strip():
            raise RiskAssessmentArchiveReasonRequired()
        if self.status is RiskAssessmentStatus.ARCHIVED:
            raise RiskAssessmentAlreadyArchived(self.id)
        self._assert_version(expected_version)
        self._assert_transition(RiskAssessmentStatus.ARCHIVED)
        return self.model_copy(
            update={
                "status": RiskAssessmentStatus.ARCHIVED,
                "archived_at": at,
                "archived_by": archived_by,
                "updated_at": at,
                "version": self.version + 1,
            }
        )

    def same_active_scope(self, other: RiskAssessment) -> bool:
        return (
            self.hazard_id == other.hazard_id
            and self.assessment_profile == other.assessment_profile
            and self.assessed_object == other.assessed_object
        )

    def build_evaluation(
        self,
        *,
        probability: Probability | int,
        severity: Severity | int,
        extra_factors: tuple[RiskFactorScore, ...] = (),
        level: RiskLevel | None = None,
        explanation: str = "",
    ) -> RiskEvaluation:
        profile = get_assessment_profile(self.assessment_profile)
        from backend.core.domain.services.assessment_profiles import (
            probability_to_score,
            severity_to_score,
        )

        p_score = probability_to_score(probability, matrix_size=profile.matrix_size)
        s_score = severity_to_score(severity, matrix_size=profile.matrix_size)
        calculated = resolve_matrix_level(
            matrix_size=profile.matrix_size,
            probability_score=p_score,
            severity_score=s_score,
        )
        factors = (
            RiskFactorScore(factor=RiskFactorCode.PROBABILITY, score=p_score),
            RiskFactorScore(factor=RiskFactorCode.SEVERITY, score=s_score),
            *extra_factors,
        )
        return self._validated_evaluation(
            RiskEvaluation(
                factors=factors,
                level=level or calculated,
                explanation=explanation
                or f"Matrix {profile.matrix_size}×{profile.matrix_size}: "
                f"P={p_score}, S={s_score} → { (level or calculated).value }",
            )
        )

    def _validated_evaluation(self, evaluation: RiskEvaluation) -> RiskEvaluation:
        profile = get_assessment_profile(self.assessment_profile)
        factor_codes = {item.factor for item in evaluation.factors}
        required = {
            RiskFactorCode.PROBABILITY,
            RiskFactorCode.SEVERITY,
        }
        if not required.issubset(factor_codes):
            raise InvalidRiskEvaluation(
                "Probability and severity factors are required."
            )
        unknown = factor_codes - set(profile.factors)
        if unknown:
            raise InvalidRiskEvaluation(
                "Evaluation contains factors not supported by the assessment profile."
            )
        return evaluation

    def _assert_editable(self) -> None:
        if self.status not in {
            RiskAssessmentStatus.DRAFT,
            RiskAssessmentStatus.UNDER_REVIEW,
        }:
            raise RiskAssessmentCannotBeModified(
                self.id,
                reason=f"status {self.status.value} is read-only",
            )

    def _assert_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise RiskAssessmentVersionConflict(
                risk_assessment_id=self.id,
                expected_version=expected_version,
                actual_version=self.version,
            )

    def _assert_transition(self, target: RiskAssessmentStatus) -> None:
        permitted = _TRANSITIONS.get(self.status.value, frozenset())
        if target.value not in permitted:
            raise InvalidRiskAssessmentTransition(
                risk_assessment_id=self.id,
                source=self.status.value,
                target=target.value,
            )
