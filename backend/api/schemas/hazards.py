from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.knowledge_objects import PaginationResponse

HazardStatusValue = Literal["draft", "active", "archived"]
HazardCategoryValue = Literal[
    "physical",
    "mechanical",
    "electrical",
    "chemical",
    "biological",
    "ergonomic",
    "psychosocial",
    "fire_and_explosion",
    "thermal",
    "radiation",
    "pressure",
    "work_at_height",
    "confined_space",
    "transport",
    "environmental",
    "dangerous_goods",
    "process_safety",
    "natural_hazard",
    "organizational",
    "other",
]
SafetyDirectionValue = Literal[
    "occupational_safety",
    "industrial_safety",
    "fire_safety",
    "environmental_safety",
    "transport_safety",
    "dangerous_goods_transport",
    "civil_defense_and_emergency",
    "sanitary_and_hygienic_safety",
    "electrical_safety",
    "radiation_safety",
]
HazardSourceValue = Literal[
    "employee_report",
    "inspection",
    "incident_investigation",
    "near_miss",
    "risk_assessment",
    "regulatory_assessment",
    "audit",
    "management_review",
    "change_management",
    "equipment_documentation",
    "sout",
    "production_control",
    "environmental_monitoring",
    "transport_control",
    "other",
]
AffectedSubjectValue = Literal[
    "employee",
    "contractor",
    "visitor",
    "driver",
    "passenger",
    "public",
    "environment",
    "equipment",
    "building",
    "transport_vehicle",
    "cargo",
    "production_process",
]


class CreateHazardRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    description: str = ""
    category: HazardCategoryValue
    safety_directions: list[SafetyDirectionValue] = Field(min_length=1)
    source: HazardSourceValue
    affected_subjects: list[AffectedSubjectValue] = Field(default_factory=list)
    location_reference: str | None = None
    process_reference: str | None = None
    equipment_reference: str | None = None
    extension_references: dict[str, str] = Field(default_factory=dict)
    identified_at: datetime | None = None


class UpdateHazardRequest(BaseModel):
    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = None
    category: HazardCategoryValue | None = None
    safety_directions: list[SafetyDirectionValue] | None = Field(default=None, min_length=1)
    source: HazardSourceValue | None = None
    affected_subjects: list[AffectedSubjectValue] | None = None
    location_reference: str | None = None
    process_reference: str | None = None
    equipment_reference: str | None = None
    extension_references: dict[str, str] | None = None


class HazardLifecycleRequest(BaseModel):
    expected_version: int = Field(ge=1)


class ArchiveHazardRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=2000)


class RestoreHazardRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=2000)


class HazardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    title: str
    description: str
    category: str
    safety_directions: list[str]
    source: str
    affected_subjects: list[str]
    location_reference: str | None = None
    process_reference: str | None = None
    equipment_reference: str | None = None
    extension_references: dict[str, str] = Field(default_factory=dict)
    status: HazardStatusValue
    identified_at: datetime
    identified_by: UUID
    reviewed_at: datetime | None = None
    reviewed_by: UUID | None = None
    archived_at: datetime | None = None
    archived_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    version: int


class HazardListResponse(BaseModel):
    items: list[HazardResponse]
    pagination: PaginationResponse
