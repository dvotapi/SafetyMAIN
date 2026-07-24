from __future__ import annotations

from backend.core.domain.entities.risk_control import RiskControl, is_terminal_inactive
from backend.core.domain.exceptions.risk_control import (
    DuplicateRiskControlCode,
    RiskControlNotFound,
    RiskControlVersionConflict,
)
from backend.core.domain.repositories.risk_control_repository import (
    RiskControlRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_control_code import RiskControlCode
from backend.core.domain.value_objects.risk_control_query import (
    RiskControlPage,
    RiskControlQuery,
)
from backend.core.domain.value_objects.safety_enums import RiskControlStatus
from backend.core.domain.value_objects.safety_ids import (
    RiskAssessmentId,
    RiskControlId,
)


class InMemoryRiskControlRepository(RiskControlRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[RiskControlId, RiskControl] = {}

    def add(self, control: RiskControl) -> None:
        existing = self.get_by_code(control.organization_id, control.code)
        if existing is not None:
            raise DuplicateRiskControlCode(
                organization_id=control.organization_id,
                code=control.code.value,
            )
        if (
            control.risk_assessment_id is not None
            and control.source_control_reference is not None
            and self.exists_for_source(
                control.organization_id,
                control.risk_assessment_id,
                control.source_control_reference,
            )
        ):
            raise DuplicateRiskControlCode(
                organization_id=control.organization_id,
                code=control.code.value,
            )
        self._by_id[control.id] = control

    def get(
        self,
        organization_id: OrganizationId,
        control_id: RiskControlId,
    ) -> RiskControl | None:
        control = self._by_id.get(control_id)
        if control is None or control.organization_id != organization_id:
            return None
        return control

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: RiskControlCode,
    ) -> RiskControl | None:
        for control in self._by_id.values():
            if (
                control.organization_id == organization_id
                and control.code.value == code.value
            ):
                return control
        return None

    def exists_for_source(
        self,
        organization_id: OrganizationId,
        risk_assessment_id: RiskAssessmentId,
        source_control_reference: str,
    ) -> bool:
        for control in self._by_id.values():
            if (
                control.organization_id == organization_id
                and control.risk_assessment_id == risk_assessment_id
                and control.source_control_reference == source_control_reference
            ):
                return True
        return False

    def list(self, query: RiskControlQuery) -> RiskControlPage:
        items = [
            item
            for item in self._by_id.values()
            if item.organization_id == query.organization_id
        ]
        if not query.include_terminal:
            items = [
                item
                for item in items
                if not is_terminal_inactive(item.lifecycle_status)
            ]
        if query.hazard_id is not None:
            items = [item for item in items if item.hazard_id == query.hazard_id]
        if query.risk_assessment_id is not None:
            items = [
                item
                for item in items
                if item.risk_assessment_id == query.risk_assessment_id
            ]
        if query.status is not None:
            items = [item for item in items if item.lifecycle_status is query.status]
        if query.hierarchy_level is not None:
            items = [
                item for item in items if item.hierarchy_level is query.hierarchy_level
            ]
        if query.control_nature is not None:
            items = [
                item for item in items if item.control_nature is query.control_nature
            ]
        if query.owner_reference is not None:
            items = [
                item
                for item in items
                if item.owner is not None
                and item.owner.owner_reference == query.owner_reference
            ]
        if query.latest_effectiveness_result is not None:
            items = [
                item
                for item in items
                if item.latest_effectiveness_result
                is query.latest_effectiveness_result
            ]
        if query.review_due_before is not None:
            items = [
                item
                for item in items
                if item.next_review_date is not None
                and item.next_review_date <= query.review_due_before
            ]
        if query.review_due_after is not None:
            items = [
                item
                for item in items
                if item.next_review_date is not None
                and item.next_review_date >= query.review_due_after
            ]
        if query.overdue_only:
            as_of = query.as_of
            if as_of is None:
                raise ValueError("as_of is required when overdue_only is true.")
            items = [item for item in items if item.is_overdue_for_review(as_of=as_of)]
        if query.awaiting_verification:
            items = [
                item
                for item in items
                if item.lifecycle_status is RiskControlStatus.IMPLEMENTED
            ]
        if query.created_from is not None:
            items = [item for item in items if item.created_at >= query.created_from]
        if query.created_to is not None:
            items = [item for item in items if item.created_at <= query.created_to]
        if query.updated_from is not None:
            items = [item for item in items if item.updated_at >= query.updated_from]
        if query.updated_to is not None:
            items = [item for item in items if item.updated_at <= query.updated_to]
        if query.search is not None and query.search.strip():
            needle = query.search.strip().lower()
            items = [
                item
                for item in items
                if needle in item.code.value.lower()
                or needle in item.title.lower()
                or needle in item.description.lower()
            ]
        items.sort(key=lambda item: (item.created_at, item.id.value), reverse=True)
        total = len(items)
        page = items[query.offset : query.offset + query.limit]
        return RiskControlPage(
            items=tuple(page),
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def save(self, control: RiskControl, *, expected_version: int) -> None:
        existing = self.get(control.organization_id, control.id)
        if existing is None:
            raise RiskControlNotFound(control.id)
        if existing.version != expected_version:
            raise RiskControlVersionConflict(
                control_id=control.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        duplicate = self.get_by_code(control.organization_id, control.code)
        if duplicate is not None and duplicate.id != control.id:
            raise DuplicateRiskControlCode(
                organization_id=control.organization_id,
                code=control.code.value,
            )
        self._by_id[control.id] = control

    def snapshot(self) -> dict[RiskControlId, RiskControl]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[RiskControlId, RiskControl]) -> None:
        self._by_id = dict(snapshot)
