from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.exceptions.risk_control import (
    InvalidRiskControlTransition,
    RiskControlCannotBeModified,
    RiskControlReasonRequired,
    RiskControlValidationError,
    RiskControlVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_control_code import RiskControlCode
from backend.core.domain.value_objects.risk_control_components import (
    ControlCompetencyRequirement,
    ControlEffectivenessVerification,
    ControlOwner,
    ControlReviewSchedule,
    ControlSource,
    EvidenceReference,
    ImplementationMilestone,
    ImplementationPlan,
    OwnerAssignmentRecord,
    RelatedEntityReference,
    ScopeReference,
    SuspensionInfo,
)
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlType,
    EffectivenessResult,
    MilestoneStatus,
    RiskControlStatus,
)
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)

_TERMINAL_INACTIVE = frozenset(
    {
        RiskControlStatus.SUPERSEDED.value,
        RiskControlStatus.ARCHIVED.value,
        RiskControlStatus.CANCELLED.value,
    }
)

_TRANSITIONS: dict[str, frozenset[str]] = {
    RiskControlStatus.DRAFT.value: frozenset(
        {
            RiskControlStatus.PLANNED.value,
            RiskControlStatus.CANCELLED.value,
            RiskControlStatus.ARCHIVED.value,
        }
    ),
    RiskControlStatus.PLANNED.value: frozenset(
        {
            RiskControlStatus.IN_IMPLEMENTATION.value,
            RiskControlStatus.DRAFT.value,
            RiskControlStatus.CANCELLED.value,
            RiskControlStatus.SUSPENDED.value,
        }
    ),
    RiskControlStatus.IN_IMPLEMENTATION.value: frozenset(
        {
            RiskControlStatus.IMPLEMENTED.value,
            RiskControlStatus.SUSPENDED.value,
            RiskControlStatus.CANCELLED.value,
        }
    ),
    RiskControlStatus.IMPLEMENTED.value: frozenset(
        {
            RiskControlStatus.VERIFIED_EFFECTIVE.value,
            RiskControlStatus.VERIFIED_INEFFECTIVE.value,
            RiskControlStatus.IN_IMPLEMENTATION.value,
            RiskControlStatus.SUSPENDED.value,
            RiskControlStatus.SUPERSEDED.value,
            RiskControlStatus.ARCHIVED.value,
        }
    ),
    RiskControlStatus.VERIFIED_EFFECTIVE.value: frozenset(
        {
            RiskControlStatus.VERIFIED_INEFFECTIVE.value,
            RiskControlStatus.SUSPENDED.value,
            RiskControlStatus.SUPERSEDED.value,
            RiskControlStatus.ARCHIVED.value,
        }
    ),
    RiskControlStatus.VERIFIED_INEFFECTIVE.value: frozenset(
        {
            RiskControlStatus.IN_IMPLEMENTATION.value,
            RiskControlStatus.SUPERSEDED.value,
            RiskControlStatus.SUSPENDED.value,
            RiskControlStatus.ARCHIVED.value,
        }
    ),
    RiskControlStatus.SUSPENDED.value: frozenset(
        {
            RiskControlStatus.DRAFT.value,
            RiskControlStatus.PLANNED.value,
            RiskControlStatus.IN_IMPLEMENTATION.value,
            RiskControlStatus.IMPLEMENTED.value,
            RiskControlStatus.VERIFIED_EFFECTIVE.value,
            RiskControlStatus.VERIFIED_INEFFECTIVE.value,
            RiskControlStatus.CANCELLED.value,
            RiskControlStatus.ARCHIVED.value,
            RiskControlStatus.SUPERSEDED.value,
        }
    ),
    RiskControlStatus.SUPERSEDED.value: frozenset({RiskControlStatus.ARCHIVED.value}),
    RiskControlStatus.ARCHIVED.value: frozenset(),
    RiskControlStatus.CANCELLED.value: frozenset({RiskControlStatus.ARCHIVED.value}),
}


class RiskControl(BaseModel):
    """Organization-scoped operational risk control aggregate root."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: RiskControlId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    code: RiskControlCode
    title: str
    description: str
    hierarchy_level: ControlType
    control_nature: ControlNature
    source: ControlSource
    hazard_id: HazardId | None = None
    risk_assessment_id: RiskAssessmentId | None = None
    scope: tuple[ScopeReference, ...] = ()
    owner: ControlOwner | None = None
    owner_history: tuple[OwnerAssignmentRecord, ...] = ()
    implementation: ImplementationPlan = Field(default_factory=ImplementationPlan)
    evidence: tuple[EvidenceReference, ...] = ()
    verifications: tuple[ControlEffectivenessVerification, ...] = ()
    review_schedule: ControlReviewSchedule = Field(default_factory=ControlReviewSchedule)
    competency_requirements: tuple[ControlCompetencyRequirement, ...] = ()
    related_entities: tuple[RelatedEntityReference, ...] = ()
    extension_data: dict[str, Any] = Field(default_factory=dict)
    lifecycle_status: RiskControlStatus = RiskControlStatus.DRAFT
    suspension: SuspensionInfo | None = None
    status_before_suspension: RiskControlStatus | None = None
    superseded_by_id: RiskControlId | None = None
    cancel_reason: str | None = None
    archive_reason: str | None = None
    verification_method_requirement: str = ""
    created_at: datetime = Field(frozen=True)
    created_by: UserId
    updated_at: datetime
    updated_by: UserId
    version: int = 1

    @field_validator("title", "description")
    @classmethod
    def require_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title and description are required.")
        return normalized

    @field_validator("version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Risk control version must be positive.")
        return value

    @property
    def latest_effectiveness_result(self) -> EffectivenessResult | None:
        if not self.verifications:
            return None
        return self.verifications[-1].result

    @property
    def next_review_date(self) -> datetime | None:
        return self.review_schedule.next_review_date

    @property
    def source_control_reference(self) -> str | None:
        return self.source.source_control_reference

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        code: RiskControlCode | str,
        title: str,
        description: str,
        hierarchy_level: ControlType,
        control_nature: ControlNature,
        source: ControlSource,
        created_by: UserId,
        created_at: datetime,
        hazard_id: HazardId | None = None,
        risk_assessment_id: RiskAssessmentId | None = None,
        scope: tuple[ScopeReference, ...] = (),
        owner: ControlOwner | None = None,
        implementation: ImplementationPlan | None = None,
        review_schedule: ControlReviewSchedule | None = None,
        competency_requirements: tuple[ControlCompetencyRequirement, ...] = (),
        related_entities: tuple[RelatedEntityReference, ...] = (),
        extension_data: dict[str, Any] | None = None,
        verification_method_requirement: str = "",
        control_id: RiskControlId | None = None,
    ) -> RiskControl:
        if not scope:
            raise RiskControlValidationError("At least one scope reference is required.")
        plan = implementation or ImplementationPlan()
        plan.validate_dates()
        owner_history: tuple[OwnerAssignmentRecord, ...] = ()
        if owner is not None:
            owner_history = (
                OwnerAssignmentRecord(
                    owner=owner,
                    changed_at=created_at,
                    changed_by=created_by,
                    reason="initial_assignment",
                ),
            )
        resolved_assessment_id = risk_assessment_id or source.risk_assessment_id
        return cls(
            id=control_id or RiskControlId(value=uuid4()),
            organization_id=organization_id,
            code=RiskControlCode(value=code) if isinstance(code, str) else code,
            title=title,
            description=description,
            hierarchy_level=hierarchy_level,
            control_nature=control_nature,
            source=source,
            hazard_id=hazard_id,
            risk_assessment_id=resolved_assessment_id,
            scope=scope,
            owner=owner,
            owner_history=owner_history,
            implementation=plan,
            review_schedule=review_schedule or ControlReviewSchedule(),
            competency_requirements=competency_requirements,
            related_entities=related_entities,
            extension_data=dict(extension_data or {}),
            verification_method_requirement=verification_method_requirement.strip(),
            created_at=created_at,
            created_by=created_by,
            updated_at=created_at,
            updated_by=created_by,
            version=1,
        )

    def update_details(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        title: str | None = None,
        description: str | None = None,
        hierarchy_level: ControlType | None = None,
        control_nature: ControlNature | None = None,
        scope: tuple[ScopeReference, ...] | None = None,
        competency_requirements: tuple[ControlCompetencyRequirement, ...] | None = None,
        related_entities: tuple[RelatedEntityReference, ...] | None = None,
        extension_data: dict[str, Any] | None = None,
        verification_method_requirement: str | None = None,
        implementation: ImplementationPlan | None = None,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status not in {
            RiskControlStatus.DRAFT,
            RiskControlStatus.PLANNED,
        }:
            raise RiskControlCannotBeModified(
                self.id,
                reason=f"status {self.lifecycle_status.value} blocks detail edits",
            )
        updates: dict[str, Any] = {
            "updated_at": at,
            "updated_by": actor_id,
            "version": self.version + 1,
        }
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if hierarchy_level is not None:
            updates["hierarchy_level"] = hierarchy_level
        if control_nature is not None:
            updates["control_nature"] = control_nature
        if scope is not None:
            if not scope:
                raise RiskControlValidationError(
                    "At least one scope reference is required."
                )
            updates["scope"] = scope
        if competency_requirements is not None:
            updates["competency_requirements"] = competency_requirements
        if related_entities is not None:
            updates["related_entities"] = related_entities
        if extension_data is not None:
            updates["extension_data"] = dict(extension_data)
        if verification_method_requirement is not None:
            updates["verification_method_requirement"] = (
                verification_method_requirement.strip()
            )
        if implementation is not None:
            implementation.validate_dates()
            updates["implementation"] = implementation
        return self.model_copy(update=updates)

    def assign_owner(
        self,
        *,
        owner: ControlOwner,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        reason: str = "",
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status in {
            RiskControlStatus.ARCHIVED,
            RiskControlStatus.CANCELLED,
            RiskControlStatus.SUPERSEDED,
        }:
            raise RiskControlCannotBeModified(
                self.id,
                reason=f"status {self.lifecycle_status.value} blocks owner changes",
            )
        record = OwnerAssignmentRecord(
            owner=owner,
            changed_at=at,
            changed_by=actor_id,
            reason=reason.strip(),
        )
        return self.model_copy(
            update={
                "owner": owner,
                "owner_history": (*self.owner_history, record),
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def plan(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        implementation: ImplementationPlan,
        verification_method_requirement: str | None = None,
    ) -> RiskControl:
        self._assert_version(expected_version)
        self._assert_transition(RiskControlStatus.PLANNED)
        if self.owner is None:
            raise RiskControlValidationError("Owner is required before planning.")
        if not self.scope:
            raise RiskControlValidationError("Scope is required before planning.")
        if implementation.target_completion_date is None:
            raise RiskControlValidationError(
                "Implementation target completion date is required."
            )
        implementation.validate_dates()
        method = (
            verification_method_requirement.strip()
            if verification_method_requirement is not None
            else self.verification_method_requirement
        )
        if not method:
            raise RiskControlValidationError(
                "Verification method requirement is required before planning."
            )
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.PLANNED,
                "implementation": implementation,
                "verification_method_requirement": method,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def return_to_draft(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status is not RiskControlStatus.PLANNED:
            raise InvalidRiskControlTransition(
                control_id=self.id,
                source=self.lifecycle_status.value,
                target=RiskControlStatus.DRAFT.value,
            )
        if self.implementation.actual_start_date is not None:
            raise RiskControlValidationError(
                "Cannot return to draft after implementation has started."
            )
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.DRAFT,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def start_implementation(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> RiskControl:
        self._assert_version(expected_version)
        self._assert_transition(RiskControlStatus.IN_IMPLEMENTATION)
        plan = self.implementation.model_copy(
            update={"actual_start_date": self.implementation.actual_start_date or at}
        )
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.IN_IMPLEMENTATION,
                "implementation": plan,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def update_progress(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        progress: int,
        summary: str | None = None,
        milestones: tuple[ImplementationMilestone, ...] | None = None,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status is not RiskControlStatus.IN_IMPLEMENTATION:
            raise RiskControlCannotBeModified(
                self.id,
                reason="progress updates require in_implementation status",
            )
        if progress < 0 or progress > 100:
            raise RiskControlValidationError("Progress must be between 0 and 100.")
        updates: dict[str, Any] = {"progress": progress}
        if summary is not None:
            updates["summary"] = summary.strip()
        if milestones is not None:
            self._validate_milestones(milestones)
            updates["milestones"] = milestones
        plan = self.implementation.model_copy(update=updates)
        return self.model_copy(
            update={
                "implementation": plan,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def add_evidence(
        self,
        *,
        evidence: EvidenceReference,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        allow_after_implemented: bool = False,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status in {
            RiskControlStatus.ARCHIVED,
            RiskControlStatus.CANCELLED,
            RiskControlStatus.SUPERSEDED,
        }:
            raise RiskControlCannotBeModified(
                self.id,
                reason=f"status {self.lifecycle_status.value} blocks evidence",
            )
        if (
            self.lifecycle_status
            in {
                RiskControlStatus.IMPLEMENTED,
                RiskControlStatus.VERIFIED_EFFECTIVE,
                RiskControlStatus.VERIFIED_INEFFECTIVE,
            }
            and not allow_after_implemented
        ):
            raise RiskControlValidationError(
                "Evidence is append-only after Implemented via explicit correction."
            )
        return self.model_copy(
            update={
                "evidence": (*self.evidence, evidence),
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def complete_implementation(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        summary: str,
        evidence_waiver_reason: str | None = None,
        allow_incomplete_milestones: bool = False,
    ) -> RiskControl:
        self._assert_version(expected_version)
        self._assert_transition(RiskControlStatus.IMPLEMENTED)
        if not summary.strip():
            raise RiskControlValidationError("Implementation summary is required.")
        if not self.evidence and not (evidence_waiver_reason or "").strip():
            raise RiskControlValidationError(
                "Implementation evidence or an explicit evidence waiver is required."
            )
        incomplete = [
            m
            for m in self.implementation.milestones
            if m.status not in {MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED}
        ]
        if incomplete and not allow_incomplete_milestones:
            raise RiskControlValidationError(
                "Mandatory milestones remain incomplete."
            )
        plan = self.implementation.model_copy(
            update={
                "actual_completion_date": at,
                "progress": 100,
                "summary": summary.strip(),
                "evidence_waiver_reason": (
                    evidence_waiver_reason.strip() if evidence_waiver_reason else None
                ),
            }
        )
        plan.validate_dates()
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.IMPLEMENTED,
                "implementation": plan,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def record_verification(
        self,
        *,
        verification: ControlEffectivenessVerification,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        schedule_next_review: bool = True,
    ) -> tuple[RiskControl, bool]:
        """Record verification. Returns (control, recommend_reassessment)."""

        self._assert_version(expected_version)
        if self.lifecycle_status not in {
            RiskControlStatus.IMPLEMENTED,
            RiskControlStatus.VERIFIED_EFFECTIVE,
            RiskControlStatus.VERIFIED_INEFFECTIVE,
        }:
            raise RiskControlValidationError(
                "Only implemented or previously verified controls may be verified."
            )
        if not verification.evidence_refs and not self.evidence:
            raise RiskControlValidationError(
                "Verification evidence is required."
            )
        recommend = False
        status = self.lifecycle_status
        schedule = self.review_schedule
        if verification.result is EffectivenessResult.EFFECTIVE:
            self._assert_transition(RiskControlStatus.VERIFIED_EFFECTIVE)
            if (
                verification.next_review_date is None
                and schedule.review_required
                and not schedule.no_review_reason
            ):
                raise RiskControlValidationError(
                    "Next review date or explicit no-review decision is required."
                )
            status = RiskControlStatus.VERIFIED_EFFECTIVE
            if schedule_next_review and verification.next_review_date is not None:
                schedule = schedule.model_copy(
                    update={
                        "next_review_date": verification.next_review_date,
                        "last_review_date": verification.performed_at,
                    }
                )
        elif verification.result is EffectivenessResult.INEFFECTIVE:
            self._assert_transition(RiskControlStatus.VERIFIED_INEFFECTIVE)
            status = RiskControlStatus.VERIFIED_INEFFECTIVE
            recommend = True
        elif verification.result is EffectivenessResult.PARTIALLY_EFFECTIVE:
            # Remain distinguishable: stay Implemented / Verified Ineffective path
            # without claiming Verified Effective.
            if self.lifecycle_status is RiskControlStatus.IMPLEMENTED:
                status = RiskControlStatus.IMPLEMENTED
            recommend = True
            if verification.next_review_date is not None:
                schedule = schedule.model_copy(
                    update={
                        "next_review_date": verification.next_review_date,
                        "last_review_date": verification.performed_at,
                    }
                )
        else:
            raise RiskControlValidationError(
                f"Unsupported verification result for lifecycle: {verification.result.value}"
            )
        updated = self.model_copy(
            update={
                "lifecycle_status": status,
                "verifications": (*self.verifications, verification),
                "review_schedule": schedule,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )
        return updated, recommend

    def schedule_review(
        self,
        *,
        schedule: ControlReviewSchedule,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status in {
            RiskControlStatus.ARCHIVED,
            RiskControlStatus.CANCELLED,
            RiskControlStatus.SUPERSEDED,
        }:
            raise RiskControlCannotBeModified(
                self.id,
                reason=f"status {self.lifecycle_status.value} blocks review scheduling",
            )
        if schedule.review_required and schedule.next_review_date is None:
            if schedule.review_frequency_days is None:
                raise RiskControlValidationError(
                    "Review frequency or next review date is required."
                )
            schedule = schedule.model_copy(
                update={
                    "next_review_date": at
                    + timedelta(days=schedule.review_frequency_days)
                }
            )
        if not schedule.review_required and not (schedule.no_review_reason or "").strip():
            raise RiskControlValidationError(
                "No-review reason is required when review is not required."
            )
        return self.model_copy(
            update={
                "review_schedule": schedule,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def complete_review(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        verification: ControlEffectivenessVerification | None = None,
        next_review_date: datetime | None = None,
    ) -> tuple[RiskControl, bool]:
        self._assert_version(expected_version)
        schedule = self.review_schedule.model_copy(
            update={
                "last_review_date": at,
                "next_review_date": next_review_date
                or (
                    at + timedelta(days=self.review_schedule.review_frequency_days)
                    if self.review_schedule.review_required
                    and self.review_schedule.review_frequency_days
                    else self.review_schedule.next_review_date
                ),
            }
        )
        updated = self.model_copy(
            update={
                "review_schedule": schedule,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )
        if verification is None:
            return updated, False
        # Version already bumped; apply verification against new version.
        return updated.record_verification(
            verification=verification,
            at=at,
            actor_id=actor_id,
            expected_version=updated.version,
            schedule_next_review=False,
        )

    def suspend(
        self,
        *,
        suspension: SuspensionInfo,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> RiskControl:
        self._assert_version(expected_version)
        self._assert_transition(RiskControlStatus.SUSPENDED)
        return self.model_copy(
            update={
                "status_before_suspension": self.lifecycle_status,
                "lifecycle_status": RiskControlStatus.SUSPENDED,
                "suspension": suspension,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def resume(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if self.lifecycle_status is not RiskControlStatus.SUSPENDED:
            raise InvalidRiskControlTransition(
                control_id=self.id,
                source=self.lifecycle_status.value,
                target="resume",
            )
        target = self.status_before_suspension or RiskControlStatus.PLANNED
        return self.model_copy(
            update={
                "lifecycle_status": target,
                "suspension": None,
                "status_before_suspension": None,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def reopen_implementation(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        reason: str,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if not reason.strip():
            raise RiskControlReasonRequired("Reopen implementation")
        self._assert_transition(RiskControlStatus.IN_IMPLEMENTATION)
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.IN_IMPLEMENTATION,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def supersede(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        replacement_control_id: RiskControlId,
        reason: str,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if not reason.strip():
            raise RiskControlReasonRequired("Supersede")
        self._assert_transition(RiskControlStatus.SUPERSEDED)
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.SUPERSEDED,
                "superseded_by_id": replacement_control_id,
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def archive(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        reason: str,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if not reason.strip():
            raise RiskControlReasonRequired("Archive")
        self._assert_transition(RiskControlStatus.ARCHIVED)
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.ARCHIVED,
                "archive_reason": reason.strip(),
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def cancel(
        self,
        *,
        at: datetime,
        actor_id: UserId,
        expected_version: int,
        reason: str,
    ) -> RiskControl:
        self._assert_version(expected_version)
        if not reason.strip():
            raise RiskControlReasonRequired("Cancel")
        self._assert_transition(RiskControlStatus.CANCELLED)
        return self.model_copy(
            update={
                "lifecycle_status": RiskControlStatus.CANCELLED,
                "cancel_reason": reason.strip(),
                "updated_at": at,
                "updated_by": actor_id,
                "version": self.version + 1,
            }
        )

    def is_overdue_for_review(self, *, as_of: datetime) -> bool:
        if self.lifecycle_status.value in _TERMINAL_INACTIVE:
            return False
        if self.lifecycle_status is RiskControlStatus.SUSPENDED:
            return False
        schedule = self.review_schedule
        if not schedule.review_required:
            return False
        if schedule.next_review_date is None:
            return False
        return schedule.next_review_date < as_of

    def suggested_next_review_date(self, *, from_date: datetime) -> datetime | None:
        if not self.review_schedule.review_required:
            return None
        days = self.review_schedule.review_frequency_days
        if days is None:
            return None
        return from_date + timedelta(days=days)

    def _validate_milestones(self, milestones: tuple[ImplementationMilestone, ...]) -> None:
        for milestone in milestones:
            if (
                milestone.status is MilestoneStatus.COMPLETED
                and milestone.completed_at is None
            ):
                raise RiskControlValidationError(
                    "Completed milestones require completion timestamps."
                )

    def _assert_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise RiskControlVersionConflict(
                control_id=self.id,
                expected_version=expected_version,
                actual_version=self.version,
            )

    def _assert_transition(self, target: RiskControlStatus) -> None:
        permitted = _TRANSITIONS.get(self.lifecycle_status.value, frozenset())
        if target.value not in permitted:
            raise InvalidRiskControlTransition(
                control_id=self.id,
                source=self.lifecycle_status.value,
                target=target.value,
            )


def is_terminal_inactive(status: RiskControlStatus) -> bool:
    return status.value in _TERMINAL_INACTIVE
