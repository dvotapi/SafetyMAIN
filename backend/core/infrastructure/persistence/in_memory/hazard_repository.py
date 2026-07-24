from __future__ import annotations

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.exceptions.hazard import (
    DuplicateHazardCode,
    HazardNotFound,
    HazardVersionConflict,
)
from backend.core.domain.repositories.hazard_repository import HazardRepositoryContract
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.hazard_code import HazardCode
from backend.core.domain.value_objects.hazard_query import HazardPage, HazardQuery
from backend.core.domain.value_objects.safety_enums import HazardStatus
from backend.core.domain.value_objects.safety_ids import HazardId


class InMemoryHazardRepository(HazardRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[HazardId, Hazard] = {}

    def add(self, hazard: Hazard) -> None:
        existing = self.get_by_code(hazard.organization_id, hazard.code)
        if existing is not None:
            raise DuplicateHazardCode(
                organization_id=hazard.organization_id,
                code=hazard.code.value,
            )
        self._by_id[hazard.id] = hazard

    def get(
        self,
        organization_id: OrganizationId,
        hazard_id: HazardId,
    ) -> Hazard | None:
        hazard = self._by_id.get(hazard_id)
        if hazard is None:
            return None
        if hazard.organization_id != organization_id:
            return None
        return hazard

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: HazardCode,
    ) -> Hazard | None:
        for hazard in self._by_id.values():
            if (
                hazard.organization_id == organization_id
                and hazard.code.value == code.value
            ):
                return hazard
        return None

    def list(self, query: HazardQuery) -> HazardPage:
        items = [
            hazard
            for hazard in self._by_id.values()
            if hazard.organization_id == query.organization_id
        ]
        if not query.include_archived:
            items = [h for h in items if h.status is not HazardStatus.ARCHIVED]
        if query.status is not None:
            items = [h for h in items if h.status is query.status]
        if query.category is not None:
            items = [h for h in items if h.category is query.category]
        if query.safety_direction is not None:
            items = [
                h for h in items if query.safety_direction in h.safety_directions
            ]
        if query.source is not None:
            items = [h for h in items if h.source is query.source]
        if query.affected_subject is not None:
            items = [
                h for h in items if query.affected_subject in h.affected_subjects
            ]
        if query.identified_from is not None:
            items = [h for h in items if h.identified_at >= query.identified_from]
        if query.identified_to is not None:
            items = [h for h in items if h.identified_at <= query.identified_to]
        if query.created_from is not None:
            items = [h for h in items if h.created_at >= query.created_from]
        if query.created_to is not None:
            items = [h for h in items if h.created_at <= query.created_to]
        if query.search is not None and query.search.strip():
            needle = query.search.strip().lower()
            items = [
                h
                for h in items
                if needle in h.code.value.lower()
                or needle in h.title.lower()
                or needle in h.description.lower()
            ]

        items.sort(key=lambda hazard: (hazard.created_at, hazard.id.value), reverse=True)
        total = len(items)
        page = items[query.offset : query.offset + query.limit]
        return HazardPage(
            items=tuple(page),
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def save(self, hazard: Hazard, *, expected_version: int) -> None:
        existing = self.get(hazard.organization_id, hazard.id)
        if existing is None:
            raise HazardNotFound(hazard.id)
        if existing.version != expected_version:
            raise HazardVersionConflict(
                hazard_id=hazard.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        duplicate = self.get_by_code(hazard.organization_id, hazard.code)
        if duplicate is not None and duplicate.id != hazard.id:
            raise DuplicateHazardCode(
                organization_id=hazard.organization_id,
                code=hazard.code.value,
            )
        self._by_id[hazard.id] = hazard

    def snapshot(self) -> dict[HazardId, Hazard]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[HazardId, Hazard]) -> None:
        self._by_id = dict(snapshot)
