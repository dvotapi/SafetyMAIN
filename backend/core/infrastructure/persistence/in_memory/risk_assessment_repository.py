from __future__ import annotations

from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import (
    DuplicateRiskAssessmentCode,
    RiskAssessmentNotFound,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.repositories.risk_assessment_repository import (
    RiskAssessmentRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.risk_assessment_components import AssessedObjectRef
from backend.core.domain.value_objects.risk_assessment_query import (
    RiskAssessmentPage,
    RiskAssessmentQuery,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessmentProfileCode,
    RiskAssessmentStatus,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId


class InMemoryRiskAssessmentRepository(RiskAssessmentRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[RiskAssessmentId, RiskAssessment] = {}

    def add(self, assessment: RiskAssessment) -> None:
        existing = self.get_by_code(assessment.organization_id, assessment.code)
        if existing is not None:
            raise DuplicateRiskAssessmentCode(
                organization_id=assessment.organization_id,
                code=assessment.code.value,
            )
        self._by_id[assessment.id] = assessment

    def get(
        self,
        organization_id: OrganizationId,
        risk_assessment_id: RiskAssessmentId,
    ) -> RiskAssessment | None:
        assessment = self._by_id.get(risk_assessment_id)
        if assessment is None:
            return None
        if assessment.organization_id != organization_id:
            return None
        return assessment

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: RiskAssessmentCode,
    ) -> RiskAssessment | None:
        for assessment in self._by_id.values():
            if (
                assessment.organization_id == organization_id
                and assessment.code.value == code.value
            ):
                return assessment
        return None

    def list(self, query: RiskAssessmentQuery) -> RiskAssessmentPage:
        items = [
            item
            for item in self._by_id.values()
            if item.organization_id == query.organization_id
        ]
        if not query.include_archived:
            items = [
                item
                for item in items
                if item.status is not RiskAssessmentStatus.ARCHIVED
            ]
        if not query.include_superseded:
            items = [
                item
                for item in items
                if item.status is not RiskAssessmentStatus.SUPERSEDED
            ]
        if query.hazard_id is not None:
            items = [item for item in items if item.hazard_id == query.hazard_id]
        if query.status is not None:
            items = [item for item in items if item.status is query.status]
        if query.assessment_profile is not None:
            items = [
                item
                for item in items
                if item.assessment_profile is query.assessment_profile
            ]
        if query.assessed_object_type is not None:
            items = [
                item
                for item in items
                if item.assessed_object.object_type.value == query.assessed_object_type
            ]
        if query.created_from is not None:
            items = [item for item in items if item.created_at >= query.created_from]
        if query.created_to is not None:
            items = [item for item in items if item.created_at <= query.created_to]
        if query.search is not None and query.search.strip():
            needle = query.search.strip().lower()
            items = [
                item
                for item in items
                if needle in item.code.value.lower() or needle in item.title.lower()
            ]
        items.sort(
            key=lambda item: (item.created_at, item.id.value),
            reverse=True,
        )
        total = len(items)
        page = items[query.offset : query.offset + query.limit]
        return RiskAssessmentPage(
            items=tuple(page),
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def list_approved_for_scope(
        self,
        *,
        organization_id: OrganizationId,
        hazard_id: HazardId,
        assessment_profile: AssessmentProfileCode,
        assessed_object: AssessedObjectRef,
    ) -> tuple[RiskAssessment, ...]:
        return tuple(
            item
            for item in self._by_id.values()
            if item.organization_id == organization_id
            and item.hazard_id == hazard_id
            and item.assessment_profile is assessment_profile
            and item.assessed_object == assessed_object
            and item.status is RiskAssessmentStatus.APPROVED
        )

    def save(self, assessment: RiskAssessment, *, expected_version: int) -> None:
        existing = self.get(assessment.organization_id, assessment.id)
        if existing is None:
            raise RiskAssessmentNotFound(assessment.id)
        if existing.version != expected_version:
            raise RiskAssessmentVersionConflict(
                risk_assessment_id=assessment.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        duplicate = self.get_by_code(assessment.organization_id, assessment.code)
        if duplicate is not None and duplicate.id != assessment.id:
            raise DuplicateRiskAssessmentCode(
                organization_id=assessment.organization_id,
                code=assessment.code.value,
            )
        self._by_id[assessment.id] = assessment

    def snapshot(self) -> dict[RiskAssessmentId, RiskAssessment]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[RiskAssessmentId, RiskAssessment]) -> None:
        self._by_id = dict(snapshot)
