from __future__ import annotations

from backend.api.schemas.hazards import HazardListResponse, HazardResponse
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.value_objects.hazard_query import HazardPage


def to_hazard_response(hazard: Hazard) -> HazardResponse:
    return HazardResponse(
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
        status=hazard.status.value,  # type: ignore[arg-type]
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


def to_hazard_list_response(page: HazardPage) -> HazardListResponse:
    return HazardListResponse(
        items=[to_hazard_response(item) for item in page.items],
        pagination=PaginationResponse(
            total=page.total,
            offset=page.offset,
            limit=page.limit,
        ),
    )
