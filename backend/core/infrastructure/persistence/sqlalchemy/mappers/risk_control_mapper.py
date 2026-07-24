from __future__ import annotations

from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_control_code import RiskControlCode
from backend.core.domain.value_objects.risk_control_components import (
    competencies_from_list,
    competencies_to_list,
    evidence_from_list,
    evidence_to_list,
    implementation_from_dict,
    implementation_to_dict,
    owner_from_dict,
    owner_history_from_list,
    owner_history_to_list,
    owner_to_dict,
    related_from_list,
    related_to_list,
    review_schedule_from_dict,
    review_schedule_to_dict,
    scope_from_list,
    scope_to_list,
    source_from_dict,
    source_to_dict,
    suspension_from_dict,
    suspension_to_dict,
    verifications_from_list,
    verifications_to_list,
)
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlType,
    RiskControlStatus,
)
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.risk_control_model import (
    RiskControlModel,
)


def to_model(control: RiskControl) -> RiskControlModel:
    latest = control.latest_effectiveness_result
    return RiskControlModel(
        id=control.id.value,
        organization_id=control.organization_id.value,
        code=control.code.value,
        title=control.title,
        description=control.description,
        hierarchy_level=control.hierarchy_level.value,
        control_nature=control.control_nature.value,
        source_type=control.source.source_type.value,
        source_reference=control.source.source_reference,
        hazard_id=None if control.hazard_id is None else control.hazard_id.value,
        risk_assessment_id=(
            None
            if control.risk_assessment_id is None
            else control.risk_assessment_id.value
        ),
        source_control_reference=control.source.source_control_reference,
        source_payload=source_to_dict(control.source),
        scope=scope_to_list(control.scope),
        owner=owner_to_dict(control.owner),
        owner_reference=(
            None if control.owner is None else control.owner.owner_reference
        ),
        owner_history=owner_history_to_list(control.owner_history),
        implementation=implementation_to_dict(control.implementation),
        evidence=evidence_to_list(control.evidence),
        verifications=verifications_to_list(control.verifications),
        review_schedule=review_schedule_to_dict(control.review_schedule),
        competency_requirements=competencies_to_list(control.competency_requirements),
        related_entities=related_to_list(control.related_entities),
        extension_data=dict(control.extension_data),
        lifecycle_status=control.lifecycle_status.value,
        latest_effectiveness_result=None if latest is None else latest.value,
        next_review_date=control.next_review_date,
        verification_method_requirement=control.verification_method_requirement,
        suspension=suspension_to_dict(control.suspension),
        status_before_suspension=(
            None
            if control.status_before_suspension is None
            else control.status_before_suspension.value
        ),
        superseded_by_id=(
            None
            if control.superseded_by_id is None
            else control.superseded_by_id.value
        ),
        cancel_reason=control.cancel_reason,
        archive_reason=control.archive_reason,
        created_at=control.created_at,
        created_by=control.created_by.value,
        updated_at=control.updated_at,
        updated_by=control.updated_by.value,
        version=control.version,
    )


def apply_to_model(model: RiskControlModel, control: RiskControl) -> None:
    mapped = to_model(control)
    for column in RiskControlModel.__table__.columns:
        if column.name == "id":
            continue
        setattr(model, column.name, getattr(mapped, column.name))


def to_domain(model: RiskControlModel) -> RiskControl:
    return RiskControl(
        id=RiskControlId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        code=RiskControlCode(value=model.code),
        title=model.title,
        description=model.description,
        hierarchy_level=ControlType(model.hierarchy_level),
        control_nature=ControlNature(model.control_nature),
        source=source_from_dict(model.source_payload or {}),
        hazard_id=None if model.hazard_id is None else HazardId(value=model.hazard_id),
        risk_assessment_id=(
            None
            if model.risk_assessment_id is None
            else RiskAssessmentId(value=model.risk_assessment_id)
        ),
        scope=scope_from_list(model.scope),
        owner=owner_from_dict(model.owner),
        owner_history=owner_history_from_list(model.owner_history),
        implementation=implementation_from_dict(model.implementation),
        evidence=evidence_from_list(model.evidence),
        verifications=verifications_from_list(model.verifications),
        review_schedule=review_schedule_from_dict(model.review_schedule),
        competency_requirements=competencies_from_list(model.competency_requirements),
        related_entities=related_from_list(model.related_entities),
        extension_data=dict(model.extension_data or {}),
        lifecycle_status=RiskControlStatus(model.lifecycle_status),
        suspension=suspension_from_dict(model.suspension),
        status_before_suspension=(
            None
            if model.status_before_suspension is None
            else RiskControlStatus(model.status_before_suspension)
        ),
        superseded_by_id=(
            None
            if model.superseded_by_id is None
            else RiskControlId(value=model.superseded_by_id)
        ),
        cancel_reason=model.cancel_reason,
        archive_reason=model.archive_reason,
        verification_method_requirement=model.verification_method_requirement or "",
        created_at=model.created_at,
        created_by=UserId(value=model.created_by),
        updated_at=model.updated_at,
        updated_by=UserId(value=model.updated_by),
        version=model.version,
    )
