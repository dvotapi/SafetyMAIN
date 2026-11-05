"""Map workbook rows to shelf places (TASK-P11-012 §3.2–3.4). Pure: no I/O.

Unknown vocabulary values are rejected with row, column and value — never guessed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.core.domain.entities.shelf_slot import SHORT_TITLE_MAX_LENGTH, ShelfSlot
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    LegalBasisConfidence,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_slot_code import ShelfSlotCode
from backend.core.domain.value_objects.shelf_values import (
    SHELF_DOCUMENT_KINDS,
    normalize_source_url,
)

# ---- headers (§3.2) ----

H_CODE = "Код"
H_SECTION = "Раздел"
H_SUBSECTION = "Подраздел"
H_TITLE = "Документ (место на полке)"
H_KIND = "Вид"
H_KEPT_ON = "Ведётся на"
H_OBLIGATION = "Обязательность"
H_CONDITION = "Условие применимости"
H_REGULATION = "Основание (НПА)"
H_CLAUSE = "Пункт / статья"
H_QUOTE = "Выдержка из НПА"
H_URL = "Ссылка на текст"
H_CONFIDENCE = "Достоверность основания"
H_CYCLE = "Цикл / периодичность"
H_PERIOD = "Период, мес"
H_STATUS = "Статус"
H_TYPE = "Тип в SafetyMAIN"
H_DOMAIN = "Домен SafetyMAIN"
H_LOCATION = "Где лежит сейчас"
H_RESPONSIBLE = "Ответственный"
H_NOTES = "Примечание"
H_LEGACY_CODE = "Код в версии 1"
H_PACKAGE = "Пакет / категория"

REQUIRED_HEADERS: tuple[str, ...] = (
    H_CODE,
    H_SECTION,
    H_SUBSECTION,
    H_TITLE,
    H_KIND,
    H_KEPT_ON,
    H_OBLIGATION,
    H_STATUS,
    H_DOMAIN,
)
OPTIONAL_HEADERS: tuple[str, ...] = (
    H_CONDITION,
    H_REGULATION,
    H_CLAUSE,
    H_QUOTE,
    H_URL,
    H_CONFIDENCE,
    H_CYCLE,
    H_PERIOD,
    H_TYPE,
    H_LOCATION,
    H_RESPONSIBLE,
    H_NOTES,
    H_LEGACY_CODE,
    H_PACKAGE,
)
# Dates belong to documents, not places (§3.2).
DOCUMENT_DATE_HEADERS: tuple[str, ...] = (
    "Дата утверждения / выдачи",
    "Следующий пересмотр",
    "Дней до пересмотра",
)

EXCLUSION_COMMENT = "Статус «Не применимо» из реестра-полки"
"""Comment of places excluded because the workbook says «Не применимо» (§3.2)."""


def normalize_header(text: str) -> str:
    """Key of a known header; a file header may add a note in parentheses, e.g.
    «Где лежит сейчас (папка 009 …)» is «Где лежит сейчас»."""
    key = _key(text)
    if key in _KNOWN_HEADERS:
        return key
    for known in _KNOWN_HEADERS:
        if key.startswith(known + " ("):
            return known
    return key


def _key(text: str) -> str:
    """Comparison key: case, ``ё``, dashes and spacing around ``/`` and ``-`` ignored."""
    value = text.strip().lower().replace("ё", "е")
    value = re.sub(r"[‐-―−]", "-", value)
    value = re.sub(r"\s+", " ", value)
    return re.sub(r"\s*([/-])\s*", r"\1", value)


_KNOWN_HEADERS = frozenset(_key(header) for header in (*REQUIRED_HEADERS, *OPTIONAL_HEADERS))


def _is_empty(text: str) -> bool:
    return _key(text) in ("", "-")


# ---- vocabularies (§3.2) ----

_KEPT_ON = {
    _key("Организация"): SlotKeptOn.ORGANIZATION,
    _key("ОПО / объект"): SlotKeptOn.FACILITY,
    _key("Событие"): SlotKeptOn.EVENT,
    _key("Работник"): SlotKeptOn.EMPLOYEE,
    _key("ТС / техника"): SlotKeptOn.ASSET,
    _key("Профессия / вид работ"): SlotKeptOn.PROFESSION,
}
_OBLIGATION = {
    _key("Обязателен"): SlotObligationLevel.MANDATORY,
    _key("Обязательна"): SlotObligationLevel.MANDATORY,
    _key("При условии"): SlotObligationLevel.CONDITIONAL,
    _key("Рекомендуется"): SlotObligationLevel.RECOMMENDED,
}
_EXCLUDED = "excluded"
_STATUS: dict[str, CuratedSlotStatus | str] = {
    _key("Есть"): CuratedSlotStatus.PRESENT,
    _key("Есть — нужен пересмотр"): CuratedSlotStatus.PRESENT_NEEDS_REVIEW,
    _key("В работе (проект)"): CuratedSlotStatus.IN_PROGRESS,
    _key("Нет"): CuratedSlotStatus.MISSING,
    _key("Уточнить"): CuratedSlotStatus.TO_CLARIFY,
    _key("Не применимо"): _EXCLUDED,
}
_KINDS = {_key(kind): kind for kind in SHELF_DOCUMENT_KINDS}
_SECTION = re.compile(r"^(\d{1,2})\s+(.+)$")
_PERIOD = re.compile(r"^(\d+)(?:[.,]0+)?$")

# ---- short title (§3.3) ----

_ABBREVIATIONS: tuple[tuple[str, str], ...] = (
    ("инструкция по охране труда", "ИОТ"),
    ("охрана труда", "ОТ"),
    ("охраны труда", "ОТ"),
    ("охране труда", "ОТ"),
    ("промышленной безопасности", "ПБ"),
    ("пожарной безопасности", "ПожБ"),
    ("транспортной безопасности", "ТрБ"),
    ("безопасности дорожного движения", "БДД"),
    ("транспортных средств", "ТС"),
    ("взрывчатых материалов", "ВМ"),
    ("приказ о назначении", "Назначение"),
    ("журнал регистрации", "Журнал"),
    ("ответственного", "отв."),
)
_ABBREVIATION_PATTERNS = tuple(
    (re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", re.IGNORECASE), short)
    for phrase, short in _ABBREVIATIONS
)
_PARENTHESES = re.compile(r"\s*\([^()]*\)")


def short_title(title: str) -> str:
    """Deterministic spine label of at most 40 characters (§3.3)."""
    text = title
    while True:
        stripped = _PARENTHESES.sub("", text)
        if stripped == text:
            break
        text = stripped
    for pattern, short in _ABBREVIATION_PATTERNS:
        text = pattern.sub(short, text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = re.sub(r"\s+", " ", title).strip()
    if len(text) <= SHORT_TITLE_MAX_LENGTH:
        return text
    cut = text[: SHORT_TITLE_MAX_LENGTH - 1]
    boundary = cut.rfind(" ")
    if boundary > 0:
        cut = cut[:boundary]
    return cut.rstrip(" ,;:-—–") + "…"


# ---- rows and results ----


@dataclass(frozen=True, slots=True)
class WorkbookRow:
    row_number: int
    values: Mapping[str, str]
    """Cell text by header as written in the file."""


@dataclass(frozen=True, slots=True)
class RowRejection:
    row_number: int
    column: str
    value: str
    reason: str


@dataclass(frozen=True, slots=True)
class MappedPlace:
    row_number: int
    code: str
    section_code: str
    section_number: int
    section_title: str
    subsection_code: str
    subsection_title: str
    safety_domain: SafetyDomain
    excluded: bool
    values: Mapping[str, Any]
    """Place fields as ``ShelfSlot`` stores them (``curated_status`` included)."""

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.values, excluded=self.excluded)


@dataclass(frozen=True, slots=True)
class MappingResult:
    places: tuple[MappedPlace, ...]
    rejections: tuple[RowRejection, ...]
    ignored_headers: tuple[str, ...] = field(default=())


def map_rows(
    rows: Iterable[WorkbookRow],
    *,
    active_type_codes: frozenset[str],
    headers: Iterable[str] = (),
) -> MappingResult:
    """Map every row; section-wide rules (domain, number, titles) apply afterwards."""
    places: list[MappedPlace] = []
    rejections: list[RowRejection] = []
    seen_codes: dict[str, int] = {}
    for row in rows:
        mapped, errors = _map_row(row, active_type_codes)
        if errors:
            rejections.extend(errors)
            continue
        assert mapped is not None
        if mapped.code in seen_codes:
            rejections.append(
                RowRejection(
                    row.row_number,
                    H_CODE,
                    mapped.code,
                    f"duplicate code (first in row {seen_codes[mapped.code]})",
                )
            )
            continue
        seen_codes[mapped.code] = row.row_number
        places.append(mapped)
    accepted, section_errors = _check_sections(places)
    ignored = tuple(
        header for header in headers if header and normalize_header(header) not in _KNOWN_HEADERS
    )
    return MappingResult(
        places=accepted,
        rejections=tuple(sorted((*rejections, *section_errors), key=lambda r: r.row_number)),
        ignored_headers=ignored,
    )


def _map_row(
    row: WorkbookRow, active_type_codes: frozenset[str]
) -> tuple[MappedPlace | None, list[RowRejection]]:
    cells = {normalize_header(header): value.strip() for header, value in row.values.items()}
    errors: list[RowRejection] = []

    def cell(header: str) -> str:
        value = cells.get(normalize_header(header), "")
        return "" if _is_empty(value) else value

    def reject(header: str, value: str, reason: str) -> None:
        errors.append(RowRejection(row.row_number, header, value, reason))

    def lookup(header: str, table: Mapping[str, Any]) -> Any:
        value = cell(header)
        if not value:
            reject(header, value, "required")
            return None
        found = table.get(_key(value))
        if found is None:
            reject(header, value, "unknown value")
        return found

    code_text = cell(H_CODE)
    code: ShelfSlotCode | None = None
    try:
        code = ShelfSlotCode(value=code_text)
    except ValueError:
        reject(H_CODE, code_text, "code must look like ТрБ.02.02")

    section_number, section_title = 0, ""
    section_match = _SECTION.match(re.sub(r"\s+", " ", cell(H_SECTION)))
    if section_match is None:
        reject(H_SECTION, cell(H_SECTION), "expected «NN Title»")
    else:
        section_number, section_title = int(section_match[1]), section_match[2].strip()

    subsection_title = cell(H_SUBSECTION)
    if not subsection_title:
        reject(H_SUBSECTION, "", "required")
    title = cell(H_TITLE)
    if not title:
        reject(H_TITLE, "", "required")

    kind = lookup(H_KIND, _KINDS)
    kept_on = lookup(H_KEPT_ON, _KEPT_ON)
    obligation = lookup(H_OBLIGATION, _OBLIGATION)
    status = lookup(H_STATUS, _STATUS)
    condition = cell(H_CONDITION)
    if obligation is SlotObligationLevel.CONDITIONAL and not condition:
        reject(H_CONDITION, "", "required for «При условии»")

    domain_text = cell(H_DOMAIN)
    domain: SafetyDomain | None = None
    if not domain_text:
        reject(H_DOMAIN, "", "required")
    else:
        raw = _key(domain_text)
        try:
            domain = SafetyDomain("transport_security" if raw == "labour" else raw)
        except ValueError:
            reject(H_DOMAIN, domain_text, "unknown value")

    period: int | None = None
    period_text = cell(H_PERIOD)
    if period_text:
        period_match = _PERIOD.match(period_text.strip("«»\" "))
        if period_match is None or int(period_match[1]) < 1:
            reject(H_PERIOD, period_text, "expected a positive number of months")
        else:
            period = int(period_match[1])

    url: str | None = None
    try:
        url = normalize_source_url(cell(H_URL))
    except ValueError as error:
        reject(H_URL, cell(H_URL), str(error))

    confidence, confidence_note = _confidence(cell(H_CONFIDENCE))
    notes = cell(H_NOTES)
    if confidence_note:
        notes = f"{notes}\n{confidence_note}" if notes else confidence_note

    type_text = cell(H_TYPE)
    type_code = type_text if type_text in active_type_codes else None

    if errors or code is None or domain is None:
        return None, errors

    values: dict[str, Any] = {
        "title": title,
        "short_title": short_title(title),
        "document_kind": kind,
        "kept_on": kept_on,
        "obligation_level": obligation,
        "applicability_condition": condition,
        "legal_basis": {
            "regulation": cell(H_REGULATION),
            "clause": cell(H_CLAUSE),
            "quote": cell(H_QUOTE),
            "source_url": url,
            "confidence": confidence,
        },
        "review_cycle_text": cell(H_CYCLE),
        "review_period_months": period,
        "curated_status": CuratedSlotStatus.TO_CLARIFY if status == _EXCLUDED else status,
        "document_type_code": type_code,
        "proposed_document_type": "" if type_code else type_text,
        "responsible_text": cell(H_RESPONSIBLE),
        "legacy_location": cell(H_LOCATION),
        "notes": notes,
        "package_code": cell(H_PACKAGE),
        "legacy_code": cell(H_LEGACY_CODE),
    }
    return (
        MappedPlace(
            row_number=row.row_number,
            code=code.value,
            section_code=code.section_code,
            section_number=section_number,
            section_title=section_title,
            subsection_code=code.subsection_code,
            subsection_title=subsection_title,
            safety_domain=domain,
            excluded=status == _EXCLUDED,
            values=values,
        ),
        [],
    )


def _confidence(text: str) -> tuple[LegalBasisConfidence, str]:
    """(confidence, note for ``notes``) per §3.2."""
    key = _key(text)
    if not key:
        return LegalBasisConfidence.NONE, ""
    if key.startswith(_key("сверено по тексту")):
        return LegalBasisConfidence.VERIFIED, ""
    if key == _key("вторичный источник"):
        return LegalBasisConfidence.SECONDARY, ""
    if key == _key("не подтверждено"):
        return LegalBasisConfidence.UNCONFIRMED, ""
    verified = key.startswith((_key("сверено"), _key("проверка отдельным агентом")))
    confidence = LegalBasisConfidence.VERIFIED if verified else LegalBasisConfidence.SECONDARY
    return confidence, f"Достоверность: {text}"


def _check_sections(
    places: list[MappedPlace],
) -> tuple[tuple[MappedPlace, ...], list[RowRejection]]:
    """Every row of a section (subsection) must agree on number, title and domain."""
    by_section: dict[str, list[MappedPlace]] = defaultdict(list)
    for place in places:
        by_section[place.section_code].append(place)
    rejected_sections: dict[str, tuple[str, str]] = {}
    for code, rows in by_section.items():
        for header, attribute in (
            (H_SECTION, lambda p: f"{p.section_number:02d} {p.section_title}"),
            (H_DOMAIN, lambda p: p.safety_domain.value),
        ):
            variants = sorted({attribute(row) for row in rows})
            if len(variants) > 1:
                rejected_sections[code] = (header, " | ".join(variants))
                break
        else:
            titles: dict[str, set[str]] = defaultdict(set)
            for row in rows:
                titles[row.subsection_code].add(row.subsection_title)
            for subsection, variants in sorted(titles.items()):
                if len(variants) > 1:
                    rejected_sections[code] = (
                        H_SUBSECTION,
                        f"{subsection}: " + " | ".join(sorted(variants)),
                    )
                    break
    numbers: dict[int, set[str]] = defaultdict(set)
    for code, rows in by_section.items():
        numbers[rows[0].section_number].add(code)
    for number, codes in numbers.items():
        if len(codes) > 1:
            for code in codes:
                rejected_sections.setdefault(
                    code, (H_SECTION, f"number {number:02d} used by {', '.join(sorted(codes))}")
                )
    errors = [
        RowRejection(
            place.row_number,
            rejected_sections[place.section_code][0],
            rejected_sections[place.section_code][1],
            f"rows of section {place.section_code} disagree",
        )
        for place in places
        if place.section_code in rejected_sections
    ]
    accepted = tuple(place for place in places if place.section_code not in rejected_sections)
    return accepted, errors


# ---- fingerprint (§3.4) ----


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value
    return value


def fingerprint(values: Mapping[str, Any], *, excluded: bool) -> str:
    """SHA-256 of the normalised mapped values; the curated status of an excluded
    place is replaced by ``excluded`` (it is frozen while excluded)."""
    payload = dict(_jsonable(values))
    payload["curated_status"] = _EXCLUDED if excluded else payload["curated_status"]
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


MAPPED_FIELDS: tuple[str, ...] = (
    "title",
    "short_title",
    "document_kind",
    "kept_on",
    "obligation_level",
    "applicability_condition",
    "legal_basis",
    "review_cycle_text",
    "review_period_months",
    "curated_status",
    "document_type_code",
    "proposed_document_type",
    "responsible_text",
    "legacy_location",
    "notes",
    "package_code",
    "legacy_code",
)


def slot_values(slot: ShelfSlot) -> dict[str, Any]:
    """The stored place in the same shape as ``MappedPlace.values``."""
    values: dict[str, Any] = {name: getattr(slot, name) for name in MAPPED_FIELDS}
    basis = slot.legal_basis
    values["legal_basis"] = {
        "regulation": basis.regulation,
        "clause": basis.clause,
        "quote": basis.quote,
        "source_url": basis.source_url,
        "confidence": basis.confidence,
    }
    return values


def slot_fingerprint(slot: ShelfSlot) -> str:
    return fingerprint(slot_values(slot), excluded=slot.is_excluded)
