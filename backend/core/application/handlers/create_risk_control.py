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
    CreateRiskControlCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_control import DuplicateRiskControlCode
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.risk_control_code import RiskControlCode


class CreateRiskControlHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: CreateRiskControlCommand) -> RiskControl:
        audit_context = require_audit_context(command.audit_context)
        code = (
            RiskControlCode(value=command.code)
            if isinstance(command.code, str)
            else command.code
        )
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_CONTROL_CREATED,
            context=audit_context,
            resource_type=AuditResourceType.RISK_CONTROL,
            target_organization_id=command.organization_id,
            metadata={"control_code": code.value},
        )

        def operation() -> RiskControl:
            existing = self._unit_of_work.risk_controls.get_by_code(
                command.organization_id,
                code,
            )
            if existing is not None:
                raise DuplicateRiskControlCode(
                    organization_id=command.organization_id,
                    code=code.value,
                )
            now = self._clock.now()
            return RiskControl.create(
                organization_id=command.organization_id,
                code=code,
                title=command.title,
                description=command.description,
                hierarchy_level=command.hierarchy_level,
                control_nature=command.control_nature,
                source=command.source,
                created_by=command.actor_id,
                created_at=now,
                hazard_id=command.hazard_id,
                risk_assessment_id=command.risk_assessment_id,
                scope=command.scope,
                owner=command.owner,
                implementation=command.implementation,
                review_schedule=command.review_schedule,
                competency_requirements=command.competency_requirements,
                related_entities=command.related_entities,
                extension_data=command.extension_data,
                verification_method_requirement=command.verification_method_requirement,
            )

        def success_spec(control: RiskControl) -> AuditRecordSpec:
            self._unit_of_work.risk_controls.add(control)
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_CONTROL_CREATED,
                context=audit_context,
                resource_type=AuditResourceType.RISK_CONTROL,
                resource_id=control.id.value,
                target_organization_id=control.organization_id,
                metadata={
                    key: value
                    for key, value in {
                        "control_id": str(control.id.value),
                        "control_code": control.code.value,
                        "hazard_id": (
                            None
                            if control.hazard_id is None
                            else str(control.hazard_id.value)
                        ),
                        "risk_id": (
                            None
                            if control.risk_assessment_id is None
                            else str(control.risk_assessment_id.value)
                        ),
                        "new_status": control.lifecycle_status.value,
                    }.items()
                    if value is not None
                },
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
