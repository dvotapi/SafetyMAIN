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
    UpdateRiskAssessmentCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import RiskAssessmentNotFound
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class UpdateRiskAssessmentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: UpdateRiskAssessmentCommand) -> RiskAssessment:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_RISK_UPDATED,
            context=audit_context,
            resource_type=AuditResourceType.RISK,
            resource_id=command.risk_assessment_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> RiskAssessment:
            assessment = self._unit_of_work.risk_assessments.get(
                command.organization_id,
                command.risk_assessment_id,
            )
            if assessment is None:
                raise RiskAssessmentNotFound(command.risk_assessment_id)
            has_updates = any(
                value is not None
                for value in (
                    command.title,
                    command.assessed_object,
                    command.assessment_date,
                    command.review_schedule,
                    command.competency_requirements,
                    command.extension_references,
                    command.controls,
                    command.inherent_risk,
                    command.residual_risk,
                    command.acceptance,
                )
            )
            updated = assessment
            expected = command.expected_version
            if has_updates:
                updated = assessment.update_details(
                    at=self._clock.now(),
                    expected_version=expected,
                    title=command.title,
                    assessed_object=command.assessed_object,
                    assessment_date=command.assessment_date,
                    review_schedule=command.review_schedule,
                    competency_requirements=command.competency_requirements,
                    extension_references=command.extension_references,
                    controls=command.controls,
                    inherent_risk=command.inherent_risk,
                    residual_risk=command.residual_risk,
                    acceptance=command.acceptance,
                )
                expected = updated.version
            if command.submit_for_review:
                updated = updated.submit_for_review(
                    at=self._clock.now(),
                    expected_version=expected,
                )
            if not has_updates and not command.submit_for_review:
                return assessment
            return updated

        def success_spec(assessment: RiskAssessment) -> AuditRecordSpec:
            if assessment.version != command.expected_version:
                self._unit_of_work.risk_assessments.save(
                    assessment,
                    expected_version=command.expected_version,
                )
            metadata: dict[str, object] = {
                "risk_id": str(assessment.id.value),
                "risk_code": assessment.code.value,
                "assessment_profile": assessment.assessment_profile.value,
                "new_status": assessment.status.value,
            }
            if assessment.inherent_risk is not None:
                metadata["inherent_level"] = assessment.inherent_risk.level.value
            if assessment.residual_risk is not None:
                metadata["residual_level"] = assessment.residual_risk.level.value
            return AuditRecordSpec(
                action=AuditAction.SAFETY_RISK_UPDATED,
                context=audit_context,
                resource_type=AuditResourceType.RISK,
                resource_id=assessment.id.value,
                target_organization_id=assessment.organization_id,
                metadata=metadata,
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
