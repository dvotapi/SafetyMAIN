from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.core.domain.exceptions.hazard import (
    HazardAlreadyActive,
    HazardAlreadyArchived,
    HazardArchiveReasonRequired,
    HazardCannotBeModified,
    HazardCategoryRequired,
    HazardNotArchived,
    HazardRestoreReasonRequired,
    HazardSafetyDirectionRequired,
    HazardTitleRequired,
    InvalidHazardTransition,
)
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

_HAZARD_TRANSITIONS: dict[str, frozenset[str]] = {
    HazardStatus.DRAFT.value: frozenset(
        {HazardStatus.ACTIVE.value, HazardStatus.ARCHIVED.value}
    ),
    HazardStatus.ACTIVE.value: frozenset({HazardStatus.ARCHIVED.value}),
    HazardStatus.ARCHIVED.value: frozenset({HazardStatus.ACTIVE.value}),
}


def _normalize_reference(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _unique_tuple[T](values: tuple[T, ...] | list[T]) -> tuple[T, ...]:
    seen: set[T] = set()
    ordered: list[T] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)


class Hazard(BaseModel):
    """Organization-scoped hazard aggregate root (infrastructure-independent)."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: HazardId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    code: HazardCode
    title: str
    description: str = ""
    category: HazardCategory
    safety_directions: tuple[SafetyDirection, ...]
    source: HazardSource
    affected_subjects: tuple[AffectedSubject, ...] = ()
    location_reference: str | None = None
    process_reference: str | None = None
    equipment_reference: str | None = None
    extension_references: dict[str, str] = Field(default_factory=dict)
    status: HazardStatus = HazardStatus.DRAFT
    identified_at: datetime
    identified_by: UserId
    reviewed_at: datetime | None = None
    reviewed_by: UserId | None = None
    archived_at: datetime | None = None
    archived_by: UserId | None = None
    created_at: datetime = Field(frozen=True)
    updated_at: datetime
    version: int = 1

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise HazardTitleRequired()
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("safety_directions")
    @classmethod
    def require_directions(
        cls, value: tuple[SafetyDirection, ...]
    ) -> tuple[SafetyDirection, ...]:
        unique = _unique_tuple(value)
        if not unique:
            raise HazardSafetyDirectionRequired()
        return unique

    @field_validator("affected_subjects")
    @classmethod
    def normalize_subjects(
        cls, value: tuple[AffectedSubject, ...]
    ) -> tuple[AffectedSubject, ...]:
        return _unique_tuple(value)

    @field_validator("location_reference", "process_reference", "equipment_reference")
    @classmethod
    def normalize_optional_refs(cls, value: str | None) -> str | None:
        return _normalize_reference(value)

    @field_validator("version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Hazard version must be positive.")
        return value

    @model_validator(mode="after")
    def require_category(self) -> Hazard:
        if self.category is None:
            raise HazardCategoryRequired()
        return self

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        code: HazardCode | str,
        title: str,
        description: str,
        category: HazardCategory,
        safety_directions: tuple[SafetyDirection, ...] | list[SafetyDirection],
        source: HazardSource,
        affected_subjects: tuple[AffectedSubject, ...] | list[AffectedSubject] = (),
        location_reference: str | None = None,
        process_reference: str | None = None,
        equipment_reference: str | None = None,
        extension_references: dict[str, str] | None = None,
        identified_at: datetime,
        identified_by: UserId,
        created_at: datetime | None = None,
        hazard_id: HazardId | None = None,
    ) -> Hazard:
        stamp = created_at or identified_at
        return cls(
            id=hazard_id or HazardId(value=uuid4()),
            organization_id=organization_id,
            code=HazardCode(value=code) if isinstance(code, str) else code,
            title=title,
            description=description,
            category=category,
            safety_directions=tuple(safety_directions),
            source=source,
            affected_subjects=tuple(affected_subjects),
            location_reference=location_reference,
            process_reference=process_reference,
            equipment_reference=equipment_reference,
            extension_references=dict(extension_references or {}),
            status=HazardStatus.DRAFT,
            identified_at=identified_at,
            identified_by=identified_by,
            created_at=stamp,
            updated_at=stamp,
            version=1,
        )

    def update_details(
        self,
        *,
        at: datetime,
        expected_version: int,
        title: str | None = None,
        description: str | None = None,
        category: HazardCategory | None = None,
        safety_directions: tuple[SafetyDirection, ...] | list[SafetyDirection] | None = None,
        source: HazardSource | None = None,
        affected_subjects: tuple[AffectedSubject, ...] | list[AffectedSubject] | None = None,
        location_reference: str | None | object = ...,
        process_reference: str | None | object = ...,
        equipment_reference: str | None | object = ...,
        extension_references: dict[str, str] | None = None,
    ) -> Hazard:
        if self.status is HazardStatus.ARCHIVED:
            raise HazardCannotBeModified(self.id, reason="archived hazards are read-only")
        if expected_version != self.version:
            from backend.core.domain.exceptions.hazard import HazardVersionConflict

            raise HazardVersionConflict(
                hazard_id=self.id,
                expected_version=expected_version,
                actual_version=self.version,
            )
        if source is not None and self.status is HazardStatus.ACTIVE and source is not self.source:
            raise HazardCannotBeModified(
                self.id,
                reason="source is immutable after activation",
            )

        updates: dict[str, Any] = {
            "updated_at": at,
            "version": self.version + 1,
        }
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if category is not None:
            updates["category"] = category
        if safety_directions is not None:
            updates["safety_directions"] = tuple(safety_directions)
        if source is not None:
            updates["source"] = source
        if affected_subjects is not None:
            updates["affected_subjects"] = tuple(affected_subjects)
        if location_reference is not ...:
            updates["location_reference"] = location_reference  # type: ignore[assignment]
        if process_reference is not ...:
            updates["process_reference"] = process_reference  # type: ignore[assignment]
        if equipment_reference is not ...:
            updates["equipment_reference"] = equipment_reference  # type: ignore[assignment]
        if extension_references is not None:
            updates["extension_references"] = dict(extension_references)
        return self.model_copy(update=updates)

    def activate(self, *, at: datetime, reviewed_by: UserId) -> Hazard:
        if self.status is HazardStatus.ACTIVE:
            raise HazardAlreadyActive(self.id)
        if self.status is HazardStatus.ARCHIVED:
            raise InvalidHazardTransition(
                hazard_id=self.id,
                source=self.status.value,
                target=HazardStatus.ACTIVE.value,
            )
        self._assert_transition(HazardStatus.ACTIVE)
        if not self.title.strip():
            raise HazardTitleRequired()
        if self.category is None:
            raise HazardCategoryRequired()
        if not self.safety_directions:
            raise HazardSafetyDirectionRequired()
        return self.model_copy(
            update={
                "status": HazardStatus.ACTIVE,
                "reviewed_at": at,
                "reviewed_by": reviewed_by,
                "updated_at": at,
                "version": self.version + 1,
            }
        )

    def archive(self, *, at: datetime, archived_by: UserId, reason: str) -> Hazard:
        if not reason.strip():
            raise HazardArchiveReasonRequired()
        if self.status is HazardStatus.ARCHIVED:
            raise HazardAlreadyArchived(self.id)
        self._assert_transition(HazardStatus.ARCHIVED)
        return self.model_copy(
            update={
                "status": HazardStatus.ARCHIVED,
                "archived_at": at,
                "archived_by": archived_by,
                "updated_at": at,
                "version": self.version + 1,
            }
        )

    def restore(self, *, at: datetime, restored_by: UserId, reason: str) -> Hazard:
        if not reason.strip():
            raise HazardRestoreReasonRequired()
        if self.status is not HazardStatus.ARCHIVED:
            raise HazardNotArchived(self.id)
        self._assert_transition(HazardStatus.ACTIVE)
        return self.model_copy(
            update={
                "status": HazardStatus.ACTIVE,
                "reviewed_at": at,
                "reviewed_by": restored_by,
                "updated_at": at,
                "version": self.version + 1,
                # Preserve archived_at/archived_by as historical markers.
                # Full archive history is retained via audit events.
            }
        )

    def _assert_transition(self, target: HazardStatus) -> None:
        permitted = _HAZARD_TRANSITIONS.get(self.status.value, frozenset())
        if target.value not in permitted:
            raise InvalidHazardTransition(
                hazard_id=self.id,
                source=self.status.value,
                target=target.value,
            )
