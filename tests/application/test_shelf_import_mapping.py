"""Workbook row mapping (TASK-P11-012 §3.2–3.4) on synthetic rows."""

from __future__ import annotations

from typing import Any

import pytest

from backend.core.application.services.shelf_import_mapping import (
    H_CODE,
    H_CONDITION,
    H_CONFIDENCE,
    H_DOMAIN,
    H_KEPT_ON,
    H_KIND,
    H_NOTES,
    H_OBLIGATION,
    H_PERIOD,
    H_SECTION,
    H_STATUS,
    H_SUBSECTION,
    H_TITLE,
    H_TYPE,
    H_URL,
    MappingResult,
    map_rows,
    short_title,
    slot_fingerprint,
)
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    LegalBasisConfidence,
    SlotKeptOn,
    SlotObligationLevel,
)
from tests.fixtures.shelf import make_section, make_slot
from tests.fixtures.shelf_workbook import place_row, workbook_rows


def _map(*rows: dict[str, Any], types: frozenset[str] = frozenset()) -> MappingResult:
    return map_rows(workbook_rows(list(rows)), active_type_codes=types)


def _one(**overrides: Any) -> Any:
    result = _map(place_row(**overrides))
    assert result.rejections == (), result.rejections
    return result.places[0]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Организация", SlotKeptOn.ORGANIZATION),
        ("ОПО / объект", SlotKeptOn.FACILITY),
        ("ОПО/объект", SlotKeptOn.FACILITY),
        ("Событие", SlotKeptOn.EVENT),
        ("Работник", SlotKeptOn.EMPLOYEE),
        ("ТС / техника", SlotKeptOn.ASSET),
        ("Профессия / вид работ", SlotKeptOn.PROFESSION),
    ],
)
def test_kept_on_vocabulary(text: str, expected: SlotKeptOn) -> None:
    assert _one(**{H_KEPT_ON: text}).values["kept_on"] is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Обязателен", SlotObligationLevel.MANDATORY),
        ("Обязательна", SlotObligationLevel.MANDATORY),
        ("Рекомендуется", SlotObligationLevel.RECOMMENDED),
    ],
)
def test_obligation_vocabulary_with_spelling_variant(
    text: str, expected: SlotObligationLevel
) -> None:
    assert _one(**{H_OBLIGATION: text}).values["obligation_level"] is expected


def test_conditional_place_needs_a_condition() -> None:
    place = _one(**{H_OBLIGATION: "При условии", H_CONDITION: "При наличии ОТИ"})
    assert place.values["obligation_level"] is SlotObligationLevel.CONDITIONAL

    result = _map(place_row(**{H_OBLIGATION: "При условии"}))
    assert result.places == ()
    assert [(r.column, r.reason) for r in result.rejections] == [
        (H_CONDITION, "required for «При условии»")
    ]


@pytest.mark.parametrize(
    ("text", "curated", "excluded"),
    [
        ("Есть", CuratedSlotStatus.PRESENT, False),
        ("Есть — нужен пересмотр", CuratedSlotStatus.PRESENT_NEEDS_REVIEW, False),
        ("Есть - нужен пересмотр", CuratedSlotStatus.PRESENT_NEEDS_REVIEW, False),
        ("В работе (проект)", CuratedSlotStatus.IN_PROGRESS, False),
        ("Нет", CuratedSlotStatus.MISSING, False),
        ("Уточнить", CuratedSlotStatus.TO_CLARIFY, False),
        ("Не применимо", CuratedSlotStatus.TO_CLARIFY, True),
    ],
)
def test_status_vocabulary(text: str, curated: CuratedSlotStatus, excluded: bool) -> None:
    place = _one(**{H_STATUS: text})
    assert place.values["curated_status"] is curated
    assert place.excluded is excluded


@pytest.mark.parametrize(
    ("text", "confidence", "note"),
    [
        ("сверено по тексту НПА", LegalBasisConfidence.VERIFIED, ""),
        ("вторичный источник", LegalBasisConfidence.SECONDARY, ""),
        ("не подтверждено", LegalBasisConfidence.UNCONFIRMED, ""),
        ("—", LegalBasisConfidence.NONE, ""),
        (None, LegalBasisConfidence.NONE, ""),
        ("сверено с консультантом", LegalBasisConfidence.VERIFIED, "Достоверность: сверено с консультантом"),
        ("проверка отдельным агентом 2026", LegalBasisConfidence.VERIFIED, "Достоверность: проверка отдельным агентом 2026"),
        ("со слов инспектора", LegalBasisConfidence.SECONDARY, "Достоверность: со слов инспектора"),
    ],
)
def test_confidence_rules(text: str | None, confidence: LegalBasisConfidence, note: str) -> None:
    place = _one(**{H_CONFIDENCE: text, H_NOTES: None})
    assert place.values["legal_basis"]["confidence"] is confidence
    assert place.values["notes"] == note


def test_free_text_confidence_is_appended_to_existing_notes() -> None:
    place = _one(**{H_CONFIDENCE: "со слов", H_NOTES: "Лежит в сейфе"})
    assert place.values["notes"] == "Лежит в сейфе\nДостоверность: со слов"


def test_labour_domain_becomes_transport_security() -> None:
    assert _one(**{H_DOMAIN: "labour"}).safety_domain is SafetyDomain.TRANSPORT_SECURITY
    assert _one(**{H_DOMAIN: "fire"}).safety_domain is SafetyDomain.FIRE


def test_section_rows_must_agree_on_the_domain() -> None:
    result = _map(
        place_row("ТрБ.01.01", **{H_DOMAIN: "labour"}),
        place_row("ТрБ.01.02", **{H_DOMAIN: "road"}),
        place_row("ПожБ.01.01"),
    )
    assert [place.code for place in result.places] == ["ПожБ.01.01"]
    assert {r.row_number for r in result.rejections} == {4, 5}
    assert {r.column for r in result.rejections} == {H_DOMAIN}


def test_section_and_subsection_parsing() -> None:
    place = _one(**{H_SECTION: "05  Взрывчатые материалы и БВР", H_SUBSECTION: "Хранение"})
    assert (place.section_number, place.section_title) == (5, "Взрывчатые материалы и БВР")
    assert (place.section_code, place.subsection_code) == ("ТрБ", "ТрБ.01")
    assert place.subsection_title == "Хранение"


def test_rows_of_one_subsection_must_agree_on_its_title() -> None:
    result = _map(
        place_row("ТрБ.01.01", **{H_SUBSECTION: "Оценка"}),
        place_row("ТрБ.01.02", **{H_SUBSECTION: "План"}),
    )
    assert result.places == ()
    assert {r.column for r in result.rejections} == {H_SUBSECTION}


def test_type_code_versus_proposed_type() -> None:
    known = _one(**{H_TYPE: "transport_plan"})
    assert known.values["proposed_document_type"] == "transport_plan"
    linked = _map(place_row(**{H_TYPE: "transport_plan"}), types=frozenset({"transport_plan"}))
    assert linked.places[0].values["document_type_code"] == "transport_plan"
    assert linked.places[0].values["proposed_document_type"] == ""
    proposed = _one(**{H_TYPE: "журнал (P11-005)"})
    assert proposed.values["document_type_code"] is None
    assert proposed.values["proposed_document_type"] == "журнал (P11-005)"


@pytest.mark.parametrize(
    ("overrides", "column"),
    [
        ({H_CODE: "ТрБ.1.01"}, H_CODE),
        ({H_CODE: None}, H_CODE),
        ({H_SECTION: "Транспортная безопасность"}, H_SECTION),
        ({H_TITLE: None}, H_TITLE),
        ({H_SUBSECTION: "—"}, H_SUBSECTION),
        ({H_KIND: "Письмо"}, H_KIND),
        ({H_KEPT_ON: "Склад"}, H_KEPT_ON),
        ({H_OBLIGATION: "Желательно"}, H_OBLIGATION),
        ({H_STATUS: "Готово"}, H_STATUS),
        ({H_DOMAIN: "labor"}, H_DOMAIN),
        ({H_DOMAIN: None}, H_DOMAIN),
        ({H_PERIOD: "пять лет"}, H_PERIOD),
        ({H_PERIOD: 0}, H_PERIOD),
        ({H_URL: "javascript:alert(1)"}, H_URL),
    ],
)
def test_unknown_or_invalid_values_are_rejected_with_row_and_column(
    overrides: dict[str, Any], column: str
) -> None:
    result = _map(place_row(**overrides))
    assert result.places == ()
    assert result.rejections and all(r.row_number == 4 for r in result.rejections)
    assert column in {r.column for r in result.rejections}


def test_duplicate_codes_are_rejected() -> None:
    result = _map(place_row("ТрБ.01.01"), place_row("ТрБ.01.01"))
    assert len(result.places) == 1
    assert [(r.row_number, r.column) for r in result.rejections] == [(5, H_CODE)]


def test_period_accepts_whole_numbers() -> None:
    assert _one(**{H_PERIOD: "36"}).values["review_period_months"] == 36
    assert _one(**{H_PERIOD: 12.0}).values["review_period_months"] == 12
    assert _one(**{H_PERIOD: None}).values["review_period_months"] is None


def test_ignored_headers_are_listed() -> None:
    result = map_rows(
        workbook_rows([place_row()]),
        active_type_codes=frozenset(),
        headers=(H_CODE, "Дней до пересмотра", "Мой столбец"),
    )
    assert result.ignored_headers == ("Дней до пересмотра", "Мой столбец")


def test_fingerprint_of_a_stored_place_equals_the_row_fingerprint() -> None:
    place = _one(**{H_CONFIDENCE: "со слов", H_URL: "https://pravo.gov.ru/x"})
    section = make_section(code="ТрБ", subsections=(("01", "Подраздел 01"),))
    from backend.core.domain.value_objects.shelf_values import SlotLegalBasis

    values = dict(place.values)
    values["legal_basis"] = SlotLegalBasis(**values["legal_basis"])
    slot = make_slot(section, code=place.code, **values)

    assert slot_fingerprint(slot) == place.fingerprint
    assert _one(**{H_NOTES: "другое"}).fingerprint != place.fingerprint


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Инструкция по охране труда для водителя", "ИОТ для водителя"),
        ("Программа вводного инструктажа по охране труда", "Программа вводного инструктажа по ОТ"),
        ("Журнал регистрации инструктажей (форма 1)", "Журнал инструктажей"),
        ("Приказ о назначении ответственного за ПБ", "Назначение отв. за ПБ"),
        ("План обеспечения транспортной безопасности", "План обеспечения ТрБ"),
        ("Декларация пожарной безопасности", "Декларация ПожБ"),
        ("Перечень транспортных средств", "Перечень ТС"),
    ],
)
def test_short_title_abbreviations(title: str, expected: str) -> None:
    assert short_title(title) == expected


def test_short_title_cuts_at_a_word_boundary() -> None:
    title = "Положение о системе управления профессиональными рисками на предприятии"
    result = short_title(title)
    assert len(result) <= 40
    assert result.endswith("…")
    assert title.startswith(result[:-1])
    assert short_title(title) == result


def test_a_header_may_carry_a_note_in_parentheses() -> None:
    from backend.core.application.services.shelf_import_mapping import WorkbookRow

    row = WorkbookRow(
        row_number=4,
        values={
            **workbook_rows([place_row()])[0].values,
            "Где лежит сейчас": "",
            "Где лежит сейчас (папка 009 …)": "Сейф 2",
        },
    )

    result = map_rows(
        [row],
        active_type_codes=frozenset(),
        headers=("Где лежит сейчас (папка 009 …)", "Документ (место на полке)"),
    )

    assert result.places[0].values["legacy_location"] == "Сейф 2"
    assert result.ignored_headers == ()
