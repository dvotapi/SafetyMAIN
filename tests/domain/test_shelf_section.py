from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.exceptions.shelf import (
    ShelfSectionValidationError,
    ShelfSectionVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from tests.fixtures.compliance_documents import FIXED_AT
from tests.fixtures.shelf import make_section


def _create(**overrides: object) -> ShelfSection:
    fields: dict[str, object] = {
        "organization_id": OrganizationId(value=uuid4()),
        "code": "ПожБ",
        "number": 8,
        "title": "Пожарная безопасность",
        "safety_domain": SafetyDomain.FIRE,
        "created_at": FIXED_AT,
    }
    fields.update(overrides)
    return ShelfSection.create(**fields)  # type: ignore[arg-type]


def test_create_section() -> None:
    section = _create()
    assert (section.code, section.number, section.version) == ("ПожБ", 8, 1)
    assert section.subsections == ()
    assert section.updated_at == FIXED_AT


@pytest.mark.parametrize("code", ["П", "ABC", "ПожБезоп", "Пож1"])
def test_section_code_must_be_two_to_six_cyrillic_letters(code: str) -> None:
    with pytest.raises(ShelfSectionValidationError):
        _create(code=code)


@pytest.mark.parametrize("number", [0, 100])
def test_section_number_range(number: int) -> None:
    with pytest.raises(ShelfSectionValidationError):
        _create(number=number)


def test_add_subsections_in_order() -> None:
    section = make_section()
    assert [item.code for item in section.subsections] == ["ТрБ.01", "ТрБ.02"]
    assert [item.position for item in section.subsections] == [0, 1]
    assert section.version == 3
    assert section.subsection("ТрБ.02") is section.subsections[1]
    assert section.subsection("ТрБ.03") is None


@pytest.mark.parametrize("code", ["ТрБ.01", "ВМ.03", "ТрБ.3", "ТрБ.03.01"])
def test_subsection_code_rules(code: str) -> None:
    section = make_section()
    with pytest.raises(ShelfSectionValidationError):
        section.add_subsection(
            code=code, title="X", at=FIXED_AT, expected_version=section.version
        )


def test_rename_section_and_subsection() -> None:
    section = make_section()
    renamed = section.rename(title="  ТрБ  ", at=FIXED_AT, expected_version=section.version)
    assert renamed.title == "ТрБ"
    renamed = renamed.rename_subsection(
        code="ТрБ.02", title="Планы", at=FIXED_AT, expected_version=renamed.version
    )
    assert renamed.subsection("ТрБ.02").title == "Планы"  # type: ignore[union-attr]
    assert renamed.subsections[1].id == section.subsections[1].id
    with pytest.raises(ShelfSectionValidationError):
        renamed.rename_subsection(
            code="ТрБ.09", title="X", at=FIXED_AT, expected_version=renamed.version
        )
    with pytest.raises(ShelfSectionValidationError):
        renamed.rename(title=" ", at=FIXED_AT, expected_version=renamed.version)


def test_version_is_checked() -> None:
    section = make_section()
    with pytest.raises(ShelfSectionVersionConflict):
        section.rename(title="X", at=FIXED_AT, expected_version=1)
