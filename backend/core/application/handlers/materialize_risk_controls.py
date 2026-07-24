from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.risk_control_lifecycle import (
    MaterializeRiskAssessmentControlsCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_assessment import RiskAssessmentNotFound
from backend.core.domain.exceptions.risk_control import (
    RiskControlAlreadyMaterialized,
    RiskControlValidationError,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.risk_assessment_components import control_to_dict
from backend.core.domain.value_objects.risk_control_components import (
    ControlSource,
    ScopeReference,
)
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlScopeType,
    RiskAssessmentStatus,
    RiskControlSourceType,
)
from backend.core.domain.value_objects.safety_ids import ControlId


class MaterializeRiskAssessmentControlsHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(
        self,
        command: MaterializeRiskAssessmentControlsCommand,
    ) -> tuple[RiskControl, ...]:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_CONTROL_MATERIALIZED,
            context=audit_context,
            resource_type=AuditResourceType.RISK_CONTROL,
            target_organization_id=command.organization_id,
            metadata={"risk_id": str(command.risk_assessment_id.value)},
        )

        def operation() -> tuple[RiskControl, ...]:
            assessment = self._unit_of_work.risk_assessments.get(
                command.organization_id,
                command.risk_assessment_id,
            )
            if assessment is None:
                raise RiskAssessmentNotFound(command.risk_assessment_id)
            allowed = {RiskAssessmentStatus.APPROVED}
            if command.allow_under_review:
                allowed.add(RiskAssessmentStatus.UNDER_REVIEW)
            if assessment.status not in allowed:
                raise RiskControlValidationError(
                    "Risk assessment status does not permit control materialization."
                )
            selected = assessment.controls
            if command.control_ids is not None:
                wanted = {ControlId(value=item) for item in command.control_ids}
                selected = tuple(
                    item for item in assessment.controls if item.id in wanted
                )
                if len(selected) != len(wanted):
                    raise RiskControlValidationError(
                        "One or more embedded controls were not found on the assessment."
                    )
            if not selected:
                raise RiskControlValidationError(
                    "No embedded controls available for materialization."
                )
            now = self._clock.now()
            created: list[RiskControl] = []
            for measure in selected:
                source_ref = str(measure.id.value)
                if self._unit_of_work.risk_controls.exists_for_source(
                    command.organization_id,
                    assessment.id,
                    source_ref,
                ):
                    raise RiskControlAlreadyMaterialized(
                        source_control_reference=source_ref
                    )
                code = f"RC-{assessment.code.value}-{source_ref[:8]}"
                control = RiskControl.create(
                    organization_id=command.organization_id,
                    code=code,
                    title=measure.description[:200],
                    description=measure.description,
                    hierarchy_level=measure.control_type,
                    control_nature=ControlNature.PREVENTIVE,
                    source=ControlSource(
                        source_type=RiskControlSourceType.RISK_ASSESSMENT,
                        source_reference=str(assessment.id.value),
                        risk_assessment_id=assessment.id,
                        source_control_reference=source_ref,
                        assessment_version=assessment.version,
                        assessment_approved_at=assessment.approved_at,
                        residual_level=(
                            None
                            if assessment.residual_risk is None
                            else assessment.residual_risk.level.value
                        ),
                        snapshot=control_to_dict(measure),
                    ),
                    created_by=command.actor_id,
                    created_at=now,
                    hazard_id=assessment.hazard_id,
                    risk_assessment_id=assessment.id,
                    scope=(
                        ScopeReference(
                            scope_type=ControlScopeType.RISK_ASSESSMENT,
                            reference=str(assessment.id.value),
                        ),
                        ScopeReference(
                            scope_type=ControlScopeType.HAZARD,
                            reference=str(assessment.hazard_id.value),
                        ),
                    ),
                    verification_method_requirement=(
                        "Initial effectiveness verification"
                    ),
                )
                created.append(control)
            return tuple(created)

        def success_spec(controls: tuple[RiskControl, ...]) -> AuditRecordSpec:
            for control in controls:
                self._unit_of_work.risk_controls.add(control)
                self._audit.record_success(
                    self._unit_of_work,
                    AuditRecordSpec(
                        action=AuditAction.SAFETY_RISK_CONTROL_CREATED,
                        context=audit_context,
                        resource_type=AuditResourceType.RISK_CONTROL,
                        resource_id=control.id.value,
                        target_organization_id=control.organization_id,
                        metadata={
                            "control_id": str(control.id.value),
                            "control_code": control.code.value,
                            "risk_id": str(command.risk_assessment_id.value),
                            "source_control_reference": (
                                control.source_control_reference or ""
                            ),
                            "new_status": control.lifecycle_status.value,
                        },
                    ),
                )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_CONTROL_MATERIALIZED,
                context=audit_context,
                resource_type=AuditResourceType.RISK,
                resource_id=command.risk_assessment_id.value,
                target_organization_id=command.organization_id,
                metadata={
                    "risk_id": str(command.risk_assessment_id.value),
                    "control_code": ",".join(item.code.value for item in controls),
                },
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
