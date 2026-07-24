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
    CreateRiskAssessmentCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.hazard import HazardNotFound
from backend.core.domain.exceptions.risk_assessment import (
    DuplicateRiskAssessmentCode,
    RiskAssessmentHazardNotActive,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.safety_enums import HazardStatus


class CreateRiskAssessmentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: CreateRiskAssessmentCommand) -> RiskAssessment:
        audit_context = require_audit_context(command.audit_context)
        code = (
            RiskAssessmentCode(value=command.code)
            if isinstance(command.code, str)
            else command.code
        )
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_CREATED,
            context=audit_context,
            resource_type=AuditResourceType.RISK,
            target_organization_id=command.organization_id,
            metadata={"risk_code": code.value},
        )

        def operation() -> RiskAssessment:
            hazard = self._unit_of_work.hazards.get(
                command.organization_id,
                command.hazard_id,
            )
            if hazard is None:
                raise HazardNotFound(command.hazard_id)
            if hazard.status is not HazardStatus.ACTIVE:
                raise RiskAssessmentHazardNotActive(hazard_id=command.hazard_id)
            existing = self._unit_of_work.risk_assessments.get_by_code(
                command.organization_id,
                code,
            )
            if existing is not None:
                raise DuplicateRiskAssessmentCode(
                    organization_id=command.organization_id,
                    code=code.value,
                )
            now = self._clock.now()
            return RiskAssessment.create(
                organization_id=command.organization_id,
                hazard_id=command.hazard_id,
                code=code,
                title=command.title,
                assessment_profile=command.assessment_profile,
                assessed_object=command.assessed_object,
                assessor_id=command.actor_id,
                assessment_date=command.assessment_date or now,
                review_schedule=command.review_schedule,
                competency_requirements=command.competency_requirements,
                extension_references=command.extension_references,
                created_at=now,
            )

        def success_spec(assessment: RiskAssessment) -> AuditRecordSpec:
            self._unit_of_work.risk_assessments.add(assessment)
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_CREATED,
                context=audit_context,
                resource_type=AuditResourceType.RISK,
                resource_id=assessment.id.value,
                target_organization_id=assessment.organization_id,
                metadata={
                    "risk_id": str(assessment.id.value),
                    "risk_code": assessment.code.value,
                    "hazard_id": str(assessment.hazard_id.value),
                    "assessment_profile": assessment.assessment_profile.value,
                    "new_status": assessment.status.value,
                },
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
