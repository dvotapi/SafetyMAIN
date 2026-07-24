from __future__ import annotations

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.hazard_code import HazardCode
from backend.core.domain.value_objects.safety_enums import (
    AffectedSubject,
    HazardCategory,
    HazardSource,
    HazardStatus,
    SafetyDirection,
)
from backend.core.domain.value_objects.safety_ids import HazardId
from backend.core.infrastructure.persistence.sqlalchemy.models.hazard_model import (
    HazardModel,
)


def to_model(hazard: Hazard) -> HazardModel:
    return HazardModel(
        id=hazard.id.value,
        organization_id=hazard.organization_id.value,
        code=hazard.code.value,
        title=hazard.title,
        description=hazard.description,
        category=hazard.category.value,
        safety_directions=[direction.value for direction in hazard.safety_directions],
        source=hazard.source.value,
        affected_subjects=[subject.value for subject in hazard.affected_subjects],
        location_reference=hazard.location_reference,
        process_reference=hazard.process_reference,
        equipment_reference=hazard.equipment_reference,
        extension_references=dict(hazard.extension_references),
        status=hazard.status.value,
        identified_at=hazard.identified_at,
        identified_by=hazard.identified_by.value,
        reviewed_at=hazard.reviewed_at,
        reviewed_by=None if hazard.reviewed_by is None else hazard.reviewed_by.value,
        archived_at=hazard.archived_at,
        archived_by=None if hazard.archived_by is None else hazard.archived_by.value,
        created_at=hazard.created_at,
        updated_at=hazard.updated_at,
        version=hazard.version,
    )


def apply_to_model(model: HazardModel, hazard: Hazard) -> None:
    model.organization_id = hazard.organization_id.value
    model.code = hazard.code.value
    model.title = hazard.title
    model.description = hazard.description
    model.category = hazard.category.value
    model.safety_directions = [direction.value for direction in hazard.safety_directions]
    model.source = hazard.source.value
    model.affected_subjects = [subject.value for subject in hazard.affected_subjects]
    model.location_reference = hazard.location_reference
    model.process_reference = hazard.process_reference
    model.equipment_reference = hazard.equipment_reference
    model.extension_references = dict(hazard.extension_references)
    model.status = hazard.status.value
    model.identified_at = hazard.identified_at
    model.identified_by = hazard.identified_by.value
    model.reviewed_at = hazard.reviewed_at
    model.reviewed_by = None if hazard.reviewed_by is None else hazard.reviewed_by.value
    model.archived_at = hazard.archived_at
    model.archived_by = None if hazard.archived_by is None else hazard.archived_by.value
    model.updated_at = hazard.updated_at
    model.version = hazard.version


def to_domain(model: HazardModel) -> Hazard:
    return Hazard(
        id=HazardId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        code=HazardCode(value=model.code),
        title=model.title,
        description=model.description,
        category=HazardCategory(model.category),
        safety_directions=tuple(
            SafetyDirection(direction) for direction in model.safety_directions
        ),
        source=HazardSource(model.source),
        affected_subjects=tuple(
            AffectedSubject(subject) for subject in (model.affected_subjects or [])
        ),
        location_reference=model.location_reference,
        process_reference=model.process_reference,
        equipment_reference=model.equipment_reference,
        extension_references=dict(model.extension_references or {}),
        status=HazardStatus(model.status),
        identified_at=model.identified_at,
        identified_by=UserId(value=model.identified_by),
        reviewed_at=model.reviewed_at,
        reviewed_by=(
            None if model.reviewed_by is None else UserId(value=model.reviewed_by)
        ),
        archived_at=model.archived_at,
        archived_by=(
            None if model.archived_by is None else UserId(value=model.archived_by)
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
        version=model.version,
    )
