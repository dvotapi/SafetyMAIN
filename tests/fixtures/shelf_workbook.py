"""Synthetic shelf workbooks for tests (the real workbook never enters the repo)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook

from backend.core.application.services.shelf_import_mapping import (
    H_CLAUSE,
    H_CODE,
    H_CONDITION,
    H_CONFIDENCE,
    H_CYCLE,
    H_DOMAIN,
    H_KEPT_ON,
    H_KIND,
    H_LEGACY_CODE,
    H_LOCATION,
    H_NOTES,
    H_OBLIGATION,
    H_PACKAGE,
    H_PERIOD,
    H_QUOTE,
    H_REGULATION,
    H_RESPONSIBLE,
    H_SECTION,
    H_STATUS,
    H_SUBSECTION,
    H_TITLE,
    H_TYPE,
    H_URL,
    WorkbookRow,
)

HEADERS: tuple[str, ...] = (
    H_CODE,
    H_SECTION,
    H_SUBSECTION,
    H_TITLE,
    H_KIND,
    H_KEPT_ON,
    H_OBLIGATION,
    H_CONDITION,
    H_REGULATION,
    H_CLAUSE,
    H_QUOTE,
    H_URL,
    H_CONFIDENCE,
    H_CYCLE,
    H_PERIOD,
    "Дата утверждения / выдачи",
    "Следующий пересмотр",
    "Дней до пересмотра",
    H_STATUS,
    H_TYPE,
    H_DOMAIN,
    H_LOCATION,
    H_RESPONSIBLE,
    H_NOTES,
    H_LEGACY_CODE,
    H_PACKAGE,
)


def place_row(code: str = "ТрБ.01.01", **overrides: Any) -> dict[str, Any]:
    """One workbook row as ``{header: value}`` with sensible defaults."""
    section = code.split(".", 1)[0]
    defaults: dict[str, Any] = {
        H_CODE: code,
        H_SECTION: {"ТрБ": "10 Транспортная безопасность", "ПожБ": "08 Пожарная безопасность"}.get(
            section, "01 Система управления"
        ),
        H_SUBSECTION: f"Подраздел {code.split('.')[1]}",
        H_TITLE: "План обеспечения транспортной безопасности объекта",
        H_KIND: "План",
        H_KEPT_ON: "ОПО / объект",
        H_OBLIGATION: "Обязателен",
        H_CONDITION: None,
        H_REGULATION: "16-ФЗ",
        H_CLAUSE: "ст. 9",
        H_QUOTE: None,
        H_URL: None,
        H_CONFIDENCE: "вторичный источник",
        H_CYCLE: "5 лет",
        H_PERIOD: 60.0,
        H_STATUS: "Нет",
        H_TYPE: None,
        H_DOMAIN: {"ТрБ": "labour", "ПожБ": "fire"}.get(section, "occupational"),
        H_LOCATION: None,
        H_RESPONSIBLE: "Специалист по ТБ",
        H_NOTES: None,
        H_LEGACY_CODE: None,
        H_PACKAGE: None,
    }
    return {**defaults, **overrides}


def workbook_rows(rows: list[dict[str, Any]], *, start: int = 4) -> tuple[WorkbookRow, ...]:
    """Rows as the reader returns them (text values), without a file."""
    from backend.core.infrastructure.importing.shelf_workbook_reader import cell_text

    return tuple(
        WorkbookRow(
            row_number=start + index,
            values={header: cell_text(row.get(header)) for header in HEADERS},
        )
        for index, row in enumerate(rows)
    )


def write_workbook(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    headers: tuple[str, ...] = HEADERS,
    header_row: int = 3,
    sheet: str = "Полка",
) -> Path:
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet
    worksheet.cell(row=1, column=1, value="Реестр-полка документов (синтетика)")
    for column, header in enumerate(headers, start=1):
        worksheet.cell(row=header_row, column=column, value=header)
    for offset, row in enumerate(rows, start=header_row + 1):
        for column, header in enumerate(headers, start=1):
            worksheet.cell(row=offset, column=column, value=row.get(header))
    workbook.create_sheet("Справочники")
    workbook.save(path)
    return path
