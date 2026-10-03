from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from backend.core.domain.entities.document_type import (
    DEFAULT_WARNING_THRESHOLDS_DAYS,
    DocumentType,
)
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from tests.fixtures.compliance_documents import FIXED_AT, make_document_type


def test_create_normalizes_text_and_applies_defaults() -> None:
    document_type = make_document_type(code="  iot_profession ", title_ru="  ИОТ  ")

    assert document_type.code == "iot_profession"
    assert document_type.title_ru == "ИОТ"
    assert document_type.warning_thresholds_days == DEFAULT_WARNING_THRESHOLDS_DAYS
    assert DEFAULT_WARNING_THRESHOLDS_DAYS == (90, 30, 14, 7)
    assert document_type.is_active is True
    assert document_type.requires_acknowledgement is False
    assert document_type.created_at == FIXED_AT
    assert document_type.updated_at == FIXED_AT


def test_create_keeps_legal_basis_and_empty_reference_becomes_none() -> None:
    document_type = DocumentType.create(
        organization_id=make_document_type().organization_id,
        code="order",
        title_ru="Приказ",
        safety_domain=SafetyDomain.LABOUR,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        legal_basis="  ТК РФ ст. 212 ",
        legal_basis_reference="   ",
        created_at=FIXED_AT,
    )

    assert document_type.legal_basis == "ТК РФ ст. 212"
    assert document_type.legal_basis_reference is None
    assert document_type.review_period_months is None


@pytest.mark.parametrize("code", ["", "   ", "x" * 65])
def test_code_must_be_present_and_at_most_64_characters(code: str) -> None:
    with pytest.raises(ValidationError):
        make_document_type(code=code)


def test_title_is_required() -> None:
    with pytest.raises(ValidationError):
        make_document_type(title_ru="  ")


@pytest.mark.parametrize(
    "periods",
    [
        {"review_period_months": 0},
        {"review_period_months": None, "validity_months": -1},
        {"review_period_months": None, "periodicity_months": 0},
    ],
)
def test_periods_must_be_positive(periods: dict[str, int | None]) -> None:
    with pytest.raises(ValidationError):
        make_document_type(**periods)


@pytest.mark.parametrize(
    "periods",
    [
        {"review_period_months": 60, "validity_months": 12},
        {"review_period_months": 60, "periodicity_months": 6},
        {"review_period_months": None, "validity_months": 12, "periodicity_months": 6},
    ],
)
def test_at_most_one_period_kind_is_allowed(periods: dict[str, int | None]) -> None:
    with pytest.raises(ValidationError):
        make_document_type(**periods)


@pytest.mark.parametrize("thresholds", [(), (30, 0), (-7,)])
def test_warning_thresholds_must_be_non_empty_and_positive(
    thresholds: tuple[int, ...],
) -> None:
    with pytest.raises(ValidationError):
        make_document_type(warning_thresholds_days=thresholds)


def test_next_review_from_adds_review_period_months() -> None:
    document_type = make_document_type(review_period_months=60)

    assert document_type.next_review_from(date(2026, 1, 31)) == date(2031, 1, 31)
    assert document_type.next_review_from(date(2024, 2, 29)) == date(2029, 2, 28)


def test_next_review_from_is_none_without_review_period() -> None:
    document_type = make_document_type(review_period_months=None, validity_months=12)

    assert document_type.next_review_from(date(2026, 1, 31)) is None


def test_review_due_cutoff_uses_largest_warning_threshold() -> None:
    document_type = make_document_type(warning_thresholds_days=(14, 90, 7))

    assert document_type.review_due_cutoff(date(2026, 10, 1)) == date(2026, 12, 30)


def test_review_due_cutoff_is_none_without_review_period() -> None:
    document_type = make_document_type(review_period_months=None, periodicity_months=12)

    assert document_type.review_due_cutoff(date(2026, 10, 1)) is None
