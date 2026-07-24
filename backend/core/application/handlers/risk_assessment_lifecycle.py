from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.risk_assessment_lifecycle import (
    ApproveRiskAssessmentCommand,
    ArchiveRiskAssessmentCommand,
    SupersedeRiskAssessmentCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import (
    RiskAssessmentNotFound,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def _load(
    unit_of_work: UnitOfWorkContract,
    command: ApproveRiskAssessmentCommand
    | ArchiveRiskAssessmentCommand
    | SupersedeRiskAssessmentCommand,
) -> RiskAssessment:
    assessment = unit_of_work.risk_assessments.get(
        command.organization_id,
        command.risk_assessment_id,
    )
    if assessment is None:
        raise RiskAssessmentNotFound(command.risk_assessment_id)
    if assessment.version != command.expected_version:
        raise RiskAssessmentVersionConflict(
            risk_assessment_id=assessment.id,
            expected_version=command.expected_version,
            actual_version=assessment.version,
        )
    return assessment


class ApproveRiskAssessmentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: ApproveRiskAssessmentCommand) -> RiskAssessment:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_APPROVED,
            context=audit_context,
            resource_type=AuditResourceType.RISK,
            resource_id=command.risk_assessment_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> tuple[RiskAssessment, str, tuple[RiskAssessment, ...]]:
            assessment = _load(self._unit_of_work, command)
            previous = assessment.status.value
            approved = assessment.approve(
                at=self._clock.now(),
                approved_by=command.actor_id,
                expected_version=command.expected_version,
                acceptance=command.acceptance,
            )
            previous_approved = self._unit_of_work.risk_assessments.list_approved_for_scope(
                organization_id=approved.organization_id,
                hazard_id=approved.hazard_id,
                assessment_profile=approved.assessment_profile,
                assessed_object=approved.assessed_object,
            )
            superseded: list[RiskAssessment] = []
            for existing in previous_approved:
                if existing.id == approved.id:
                    continue
                superseded.append(
                    existing.supersede(
                        at=self._clock.now(),
                        superseded_by_id=approved.id,
                        expected_version=existing.version,
                    )
                )
            return approved, previous, tuple(superseded)

        def success_spec(
            result: tuple[RiskAssessment, str, tuple[RiskAssessment, ...]],
        ) -> AuditRecordSpec:
            approved, previous, superseded = result
            self._unit_of_work.risk_assessments.save(
                approved,
                expected_version=command.expected_version,
            )
            for item in superseded:
                # expected_version matches pre-supersede version used in domain call
                self._unit_of_work.risk_assessments.save(
                    item,
                    expected_version=item.version - 1,
                )
                self._audit.record_success(
                    self._unit_of_work,
                    AuditRecordSpec(
                        action=AuditAction.SAFETY_RISK_SUPERSEDED,
                        context=audit_context,
                        resource_type=AuditResourceType.RISK,
                        resource_id=item.id.value,
                        target_organization_id=item.organization_id,
                        metadata={
                            "risk_id": str(item.id.value),
                            "risk_code": item.code.value,
                            "previous_status": "approved",
                            "new_status": item.status.value,
                        },
                    ),
                )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_APPROVED,
                context=audit_context,
                resource_type=AuditResourceType.RISK,
                resource_id=approved.id.value,
                target_organization_id=approved.organization_id,
                metadata={
                    key: value
                    for key, value in {
                        "risk_id": str(approved.id.value),
                        "risk_code": approved.code.value,
                        "previous_status": previous,
                        "new_status": approved.status.value,
                        "assessment_profile": approved.assessment_profile.value,
                        "inherent_level": (
                            approved.inherent_risk.level.value
                            if approved.inherent_risk
                            else None
                        ),
                        "residual_level": (
                            approved.residual_risk.level.value
                            if approved.residual_risk
                            else None
                        ),
                    }.items()
                    if value is not None
                },
            )

        approved, _previous, _superseded = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return approved


class ArchiveRiskAssessmentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: ArchiveRiskAssessmentCommand) -> RiskAssessment:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_ARCHIVED,
            context=audit_context,
            resource_type=AuditResourceType.RISK,
            resource_id=command.risk_assessment_id.value,
            target_organization_id=command.organization_id,
            metadata={"reason": command.reason},
        )

        def operation() -> tuple[RiskAssessment, str]:
            assessment = _load(self._unit_of_work, command)
            previous = assessment.status.value
            archived = assessment.archive(
                at=self._clock.now(),
                archived_by=command.actor_id,
                reason=command.reason,
                expected_version=command.expected_version,
            )
            return archived, previous

        def success_spec(result: tuple[RiskAssessment, str]) -> AuditRecordSpec:
            assessment, previous = result
            self._unit_of_work.risk_assessments.save(
                assessment,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_ARCHIVED,
                context=audit_context,
                resource_type=AuditResourceType.RISK,
                resource_id=assessment.id.value,
                target_organization_id=assessment.organization_id,
                metadata={
                    "risk_id": str(assessment.id.value),
                    "risk_code": assessment.code.value,
                    "previous_status": previous,
                    "new_status": assessment.status.value,
                    "reason": command.reason,
                },
            )

        assessment, _previous = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return assessment


class SupersedeRiskAssessmentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: SupersedeRiskAssessmentCommand) -> RiskAssessment:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_SUPERSEDED,
            context=audit_context,
            resource_type=AuditResourceType.RISK,
            resource_id=command.risk_assessment_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> tuple[RiskAssessment, str]:
            assessment = _load(self._unit_of_work, command)
            previous = assessment.status.value
            superseded = assessment.supersede(
                at=self._clock.now(),
                superseded_by_id=command.superseded_by_id,
                expected_version=command.expected_version,
            )
            return superseded, previous

        def success_spec(result: tuple[RiskAssessment, str]) -> AuditRecordSpec:
            assessment, previous = result
            self._unit_of_work.risk_assessments.save(
                assessment,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_SUPERSEDED,
                context=audit_context,
                resource_type=AuditResourceType.RISK,
                resource_id=assessment.id.value,
                target_organization_id=assessment.organization_id,
                metadata={
                    "risk_id": str(assessment.id.value),
                    "risk_code": assessment.code.value,
                    "previous_status": previous,
                    "new_status": assessment.status.value,
                },
            )

        assessment, _previous = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return assessment
