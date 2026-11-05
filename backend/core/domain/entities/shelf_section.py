from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from backend.core.domain.exceptions.shelf import (
    ShelfSectionValidationError,
    ShelfSectionVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.safety_ids import (
    ShelfSectionId,
    ShelfSubsectionId,
)
from backend.core.domain.value_objects.shelf_slot_code import (
    SHELF_SECTION_CODE_PATTERN,
    SHELF_SUBSECTION_CODE_PATTERN,
)


def _required_title(value: str, what: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{what} title is required.")
    if len(normalized) > 500:
        raise ValueError(f"{what} title must be at most 500 characters.")
    return normalized


class ShelfSubsection(BaseModel):
    """Sub-shelf of a section, code `SECTION.SS` (e.g. `ТрБ.02`)."""

    model_config = ConfigDict(frozen=True)

    id: ShelfSubsectionId
    code: str
    title: str
    position: int

    @field_validator("code")
    @classmethod
    def require_code(cls, value: str) -> str:
        if not SHELF_SUBSECTION_CODE_PATTERN.fullmatch(value):
            raise ValueError("Shelf subsection code must look like SECTION.SS.")
        return value

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        return _required_title(value, "Shelf subsection")

    @field_validator("position")
    @classmethod
    def require_position(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Shelf subsection position must not be negative.")
        return value


class ShelfSection(BaseModel):
    """Organization-scoped shelf section (one bookcase), e.g. `ТрБ` «Транспортная безопасность».

    Sections and subsections are only created or renamed, never removed.
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: ShelfSectionId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    code: str = Field(frozen=True)
    number: int
    title: str
    safety_domain: SafetyDomain
    subsections: tuple[ShelfSubsection, ...] = ()
    created_at: datetime = Field(frozen=True)
    updated_at: datetime
    version: int = 1

    @field_validator("code")
    @classmethod
    def require_code(cls, value: str) -> str:
        if not SHELF_SECTION_CODE_PATTERN.fullmatch(value):
            raise ValueError("Shelf section code must be 2–6 Cyrillic letters.")
        return value

    @field_validator("number")
    @classmethod
    def require_number(cls, value: int) -> int:
        if not 1 <= value <= 99:
            raise ValueError("Shelf section number must be between 1 and 99.")
        return value

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        return _required_title(value, "Shelf section")

    @field_validator("version")
    @classmethod
    def require_positive_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Shelf section version must be positive.")
        return value

    @model_validator(mode="after")
    def check_subsections(self) -> ShelfSection:
        codes = [subsection.code for subsection in self.subsections]
        if len(set(codes)) != len(codes):
            raise ValueError("Shelf subsection codes must be unique within a section.")
        positions = [subsection.position for subsection in self.subsections]
        if len(set(positions)) != len(positions):
            raise ValueError("Shelf subsection positions must be unique within a section.")
        prefix = f"{self.code}."
        if any(not code.startswith(prefix) for code in codes):
            raise ValueError("Shelf subsection codes must start with the section code.")
        return self

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        code: str,
        number: int,
        title: str,
        safety_domain: SafetyDomain,
        created_at: datetime,
        section_id: ShelfSectionId | None = None,
    ) -> ShelfSection:
        return _validated(
            id=section_id or ShelfSectionId(value=uuid4()),
            organization_id=organization_id,
            code=code,
            number=number,
            title=title,
            safety_domain=safety_domain,
            subsections=(),
            created_at=created_at,
            updated_at=created_at,
            version=1,
        )

    def subsection(self, code: str) -> ShelfSubsection | None:
        for subsection in self.subsections:
            if subsection.code == code:
                return subsection
        return None

    def rename(self, *, title: str, at: datetime, expected_version: int) -> ShelfSection:
        self._assert_version(expected_version)
        return self._mutated(at=at, title=title)

    def add_subsection(
        self,
        *,
        code: str,
        title: str,
        at: datetime,
        expected_version: int,
        subsection_id: ShelfSubsectionId | None = None,
    ) -> ShelfSection:
        """Append a subsection; its position follows the existing ones."""
        self._assert_version(expected_version)
        if self.subsection(code) is not None:
            raise ShelfSectionValidationError(
                f"Shelf subsection code already exists in the section: {code}."
            )
        position = max((item.position for item in self.subsections), default=-1) + 1
        try:
            subsection = ShelfSubsection(
                id=subsection_id or ShelfSubsectionId(value=uuid4()),
                code=code,
                title=title,
                position=position,
            )
        except ValidationError as error:
            raise ShelfSectionValidationError(_message(error)) from error
        return self._mutated(at=at, subsections=(*self.subsections, subsection))

    def rename_subsection(
        self, *, code: str, title: str, at: datetime, expected_version: int
    ) -> ShelfSection:
        self._assert_version(expected_version)
        current = self.subsection(code)
        if current is None:
            raise ShelfSectionValidationError(f"Shelf subsection was not found: {code}.")
        try:
            renamed = current.model_copy(update={"title": _required_title(title, "Shelf subsection")})
        except ValueError as error:
            raise ShelfSectionValidationError(str(error)) from error
        return self._mutated(
            at=at,
            subsections=tuple(
                renamed if item.code == code else item for item in self.subsections
            ),
        )

    def _mutated(self, *, at: datetime, **updates: Any) -> ShelfSection:
        return _validated(
            **{**dict(self), **updates, "updated_at": at, "version": self.version + 1}
        )

    def _assert_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise ShelfSectionVersionConflict(
                section_id=self.id,
                expected_version=expected_version,
                actual_version=self.version,
            )


def _message(error: ValidationError) -> str:
    detail = error.errors()[0]
    return str(detail.get("ctx", {}).get("error") or detail["msg"])


def _validated(**fields: Any) -> ShelfSection:
    try:
        return ShelfSection(**fields)
    except ValidationError as error:
        raise ShelfSectionValidationError(_message(error)) from error
