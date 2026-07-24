from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.risk_control_lifecycle import (
    AddRiskControlEvidenceCommand,
    ArchiveRiskControlCommand,
    AssignRiskControlOwnerCommand,
    CancelRiskControlCommand,
    CompleteRiskControlImplementationCommand,
    CompleteRiskControlReviewCommand,
    PlanRiskControlCommand,
    RecordRiskControlVerificationCommand,
    ResumeRiskControlCommand,
    ScheduleRiskControlReviewCommand,
    StartRiskControlImplementationCommand,
    SupersedeRiskControlCommand,
    SuspendRiskControlCommand,
    UpdateRiskControlCommand,
    UpdateRiskControlProgressCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_control import (
    RiskControlNotFound,
    RiskControlVersionConflict,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.safety_enums import EffectivenessResult


def _load(
    unit_of_work: UnitOfWorkContract,
    *,
    organization_id: Any,
    control_id: Any,
    expected_version: int,
) -> RiskControl:
    control = unit_of_work.risk_controls.get(organization_id, control_id)
    if control is None:
        raise RiskControlNotFound(control_id)
    if control.version != expected_version:
        raise RiskControlVersionConflict(
            control_id=control.id,
            expected_version=expected_version,
            actual_version=control.version,
        )
    return control


def _meta(control: RiskControl, **extra: str | None) -> dict[str, str]:
    payload: dict[str, str] = {
        "control_id": str(control.id.value),
        "control_code": control.code.value,
        "previous_status": extra.pop("previous_status", control.lifecycle_status.value)
        or control.lifecycle_status.value,
        "new_status": control.lifecycle_status.value,
        "expected_version": str(control.version - 1),
        "resulting_version": str(control.version),
    }
    if control.hazard_id is not None:
        payload["hazard_id"] = str(control.hazard_id.value)
    if control.risk_assessment_id is not None:
        payload["risk_id"] = str(control.risk_assessment_id.value)
    for key, value in extra.items():
        if value is not None:
            payload[key] = value
    return payload


class _MutatingHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def _run(
        self,
        *,
        action: AuditAction,
        organization_id: Any,
        control_id: Any,
        expected_version: int,
        actor_id: Any,
        audit_context: Any,
        mutate: Callable[[RiskControl], RiskControl | tuple[RiskControl, bool]],
        extra_meta: Callable[[RiskControl], dict[str, str]] | None = None,
    ) -> RiskControl:
        context = require_audit_context(audit_context)
        failure_spec = AuditRecordSpec(
            action=action,
            context=context,
            resource_type=AuditResourceType.RISK_CONTROL,
            resource_id=control_id.value,
            target_organization_id=organization_id,
        )

        def operation() -> RiskControl:
            control = _load(
                self._unit_of_work,
                organization_id=organization_id,
                control_id=control_id,
                expected_version=expected_version,
            )
            result = mutate(control)
            if isinstance(result, tuple):
                return result[0]
            return result

        def success_spec(control: RiskControl) -> AuditRecordSpec:
            self._unit_of_work.risk_controls.save(
                control,
                expected_version=expected_version,
            )
            metadata = _meta(control)
            if extra_meta is not None:
                metadata.update(extra_meta(control))
            return AuditRecordSpec(
                action=action,
                context=context,
                resource_type=AuditResourceType.RISK_CONTROL,
                resource_id=control.id.value,
                target_organization_id=control.organization_id,
                metadata=metadata,
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )


class UpdateRiskControlHandler(_MutatingHandler):
    def handle(self, command: UpdateRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_UPDATED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.update_details(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                title=command.title,
                description=command.description,
                hierarchy_level=command.hierarchy_level,
                control_nature=command.control_nature,
                scope=command.scope,
                competency_requirements=command.competency_requirements,
                related_entities=command.related_entities,
                extension_data=command.extension_data,
                verification_method_requirement=command.verification_method_requirement,
                implementation=command.implementation,
            ),
        )


class AssignRiskControlOwnerHandler(_MutatingHandler):
    def handle(self, command: AssignRiskControlOwnerCommand) -> RiskControl:
        context = require_audit_context(command.audit_context)

        def operation() -> tuple[RiskControl, str | None]:
            control = _load(
                self._unit_of_work,
                organization_id=command.organization_id,
                control_id=command.control_id,
                expected_version=command.expected_version,
            )
            prev = None if control.owner is None else control.owner.owner_reference
            updated = control.assign_owner(
                owner=command.owner,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            )
            return updated, prev

        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_CONTROL_OWNER_ASSIGNED,
            context=context,
            resource_type=AuditResourceType.RISK_CONTROL,
            resource_id=command.control_id.value,
            target_organization_id=command.organization_id,
        )

        def success_spec(result: tuple[RiskControl, str | None]) -> AuditRecordSpec:
            control, prev = result
            self._unit_of_work.risk_controls.save(
                control,
                expected_version=command.expected_version,
            )
            chosen = (
                AuditAction.SAFETY_RISK_CONTROL_OWNER_CHANGED
                if prev is not None
                else AuditAction.SAFETY_RISK_CONTROL_OWNER_ASSIGNED
            )
            return AuditRecordSpec(
                action=chosen,
                context=context,
                resource_type=AuditResourceType.RISK_CONTROL,
                resource_id=control.id.value,
                target_organization_id=control.organization_id,
                metadata=_meta(
                    control,
                    owner_reference=command.owner.owner_reference,
                ),
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )[0]


class PlanRiskControlHandler(_MutatingHandler):
    def handle(self, command: PlanRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_PLANNED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.plan(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                implementation=command.implementation,
                verification_method_requirement=command.verification_method_requirement,
            ),
        )


class StartRiskControlImplementationHandler(_MutatingHandler):
    def handle(self, command: StartRiskControlImplementationCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_IMPLEMENTATION_STARTED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.start_implementation(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
        )


class UpdateRiskControlProgressHandler(_MutatingHandler):
    def handle(self, command: UpdateRiskControlProgressCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_PROGRESS_UPDATED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.update_progress(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                progress=command.progress,
                summary=command.summary,
                milestones=command.milestones,
            ),
        )


class AddRiskControlEvidenceHandler(_MutatingHandler):
    def handle(self, command: AddRiskControlEvidenceCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_EVIDENCE_ADDED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.add_evidence(
                evidence=command.evidence,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                allow_after_implemented=command.allow_after_implemented,
            ),
        )


class CompleteRiskControlImplementationHandler(_MutatingHandler):
    def handle(self, command: CompleteRiskControlImplementationCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_IMPLEMENTED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.complete_implementation(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                summary=command.summary,
                evidence_waiver_reason=command.evidence_waiver_reason,
                allow_incomplete_milestones=command.allow_incomplete_milestones,
            ),
        )


class RecordRiskControlVerificationHandler(_MutatingHandler):
    def handle(self, command: RecordRiskControlVerificationCommand) -> RiskControl:
        context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_CONTROL_VERIFICATION_RECORDED,
            context=context,
            resource_type=AuditResourceType.RISK_CONTROL,
            resource_id=command.control_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> tuple[RiskControl, bool, str]:
            control = _load(
                self._unit_of_work,
                organization_id=command.organization_id,
                control_id=command.control_id,
                expected_version=command.expected_version,
            )
            previous = control.lifecycle_status.value
            updated, recommend = control.record_verification(
                verification=command.verification,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            return updated, recommend, previous

        def success_spec(
            result: tuple[RiskControl, bool, str],
        ) -> AuditRecordSpec:
            control, _recommend, previous = result
            self._unit_of_work.risk_controls.save(
                control,
                expected_version=command.expected_version,
            )
            result_value = command.verification.result
            if result_value is EffectivenessResult.EFFECTIVE:
                action = AuditAction.SAFETY_RISK_CONTROL_VERIFIED_EFFECTIVE
            elif result_value is EffectivenessResult.PARTIALLY_EFFECTIVE:
                action = AuditAction.SAFETY_RISK_CONTROL_VERIFIED_PARTIALLY_EFFECTIVE
            elif result_value is EffectivenessResult.INEFFECTIVE:
                action = AuditAction.SAFETY_RISK_CONTROL_VERIFIED_INEFFECTIVE
            else:
                action = AuditAction.SAFETY_RISK_CONTROL_VERIFICATION_RECORDED
            return AuditRecordSpec(
                action=action,
                context=context,
                resource_type=AuditResourceType.RISK_CONTROL,
                resource_id=control.id.value,
                target_organization_id=control.organization_id,
                metadata=_meta(
                    control,
                    previous_status=previous,
                    effectiveness_result=result_value.value,
                ),
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )[0]


class ScheduleRiskControlReviewHandler(_MutatingHandler):
    def handle(self, command: ScheduleRiskControlReviewCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_REVIEW_SCHEDULED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.schedule_review(
                schedule=command.schedule,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
        )


class CompleteRiskControlReviewHandler(_MutatingHandler):
    def handle(self, command: CompleteRiskControlReviewCommand) -> RiskControl:
        context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_CONTROL_REVIEW_COMPLETED,
            context=context,
            resource_type=AuditResourceType.RISK_CONTROL,
            resource_id=command.control_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> RiskControl:
            control = _load(
                self._unit_of_work,
                organization_id=command.organization_id,
                control_id=command.control_id,
                expected_version=command.expected_version,
            )
            updated, _ = control.complete_review(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                verification=command.verification,
                next_review_date=command.next_review_date,
            )
            return updated

        def success_spec(control: RiskControl) -> AuditRecordSpec:
            # complete_review may bump version twice when verification provided
            self._unit_of_work.risk_controls.save(
                control,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_CONTROL_REVIEW_COMPLETED,
                context=context,
                resource_type=AuditResourceType.RISK_CONTROL,
                resource_id=control.id.value,
                target_organization_id=control.organization_id,
                metadata=_meta(control),
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )


class SuspendRiskControlHandler(_MutatingHandler):
    def handle(self, command: SuspendRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_SUSPENDED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.suspend(
                suspension=command.suspension,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
            extra_meta=lambda control: {"reason": command.suspension.reason},
        )


class ResumeRiskControlHandler(_MutatingHandler):
    def handle(self, command: ResumeRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_RESUMED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.resume(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
        )


class SupersedeRiskControlHandler(_MutatingHandler):
    def handle(self, command: SupersedeRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_SUPERSEDED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.supersede(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                replacement_control_id=command.replacement_control_id,
                reason=command.reason,
            ),
            extra_meta=lambda control: {"reason": command.reason},
        )


class ArchiveRiskControlHandler(_MutatingHandler):
    def handle(self, command: ArchiveRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_ARCHIVED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.archive(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            ),
            extra_meta=lambda control: {"reason": command.reason},
        )


class CancelRiskControlHandler(_MutatingHandler):
    def handle(self, command: CancelRiskControlCommand) -> RiskControl:
        return self._run(
            action=AuditAction.SAFETY_RISK_CONTROL_CANCELLED,
            organization_id=command.organization_id,
            control_id=command.control_id,
            expected_version=command.expected_version,
            actor_id=command.actor_id,
            audit_context=command.audit_context,
            mutate=lambda control: control.cancel(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            ),
            extra_meta=lambda control: {"reason": command.reason},
        )
