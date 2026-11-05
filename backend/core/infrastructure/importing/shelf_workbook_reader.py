"""Read the shelf workbook (sheet «Полка») into plain rows (TASK-P11-012 §3.1).

The only code that touches the ``.xlsx`` file. It finds the header row by header
names and returns cell values as text; mapping and validation happen in
``backend/core/application/services/shelf_import_mapping.py``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

from backend.core.application.services.shelf_import_mapping import (
    REQUIRED_HEADERS,
    WorkbookRow,
    normalize_header,
)

SHEET_NAME = "Полка"
HEADER_SEARCH_ROWS = 10
MAX_FILE_BYTES = 20 * 1024 * 1024


class WorkbookReadError(Exception):
    """The file cannot be used as a shelf workbook; the message is user-facing."""


@dataclass(frozen=True, slots=True)
class WorkbookContent:
    rows: tuple[WorkbookRow, ...]
    headers: tuple[str, ...]
    """Header texts as found in the file, in column order."""
    file_sha256: str


def read_shelf_workbook(path: Path) -> WorkbookContent:
    if path.suffix.lower() != ".xlsx":
        raise WorkbookReadError(f"Expected an .xlsx file, got {path.name}.")
    if not path.is_file():
        raise WorkbookReadError(f"File not found: {path}.")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise WorkbookReadError(f"File is larger than {MAX_FILE_BYTES // (1024 * 1024)} MB.")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if SHEET_NAME not in workbook.sheetnames:
            raise WorkbookReadError(f"Sheet «{SHEET_NAME}» not found.")
        sheet = workbook[SHEET_NAME]
        all_rows = [tuple(row) for row in sheet.iter_rows(values_only=True)]
    finally:
        workbook.close()

    header_index = _find_header_row(all_rows)
    headers = tuple(cell_text(cell) for cell in all_rows[header_index])
    rows: list[WorkbookRow] = []
    for offset, cells in enumerate(all_rows[header_index + 1 :], start=header_index + 2):
        values = {
            header: cell_text(cells[position] if position < len(cells) else None)
            for position, header in enumerate(headers)
            if header
        }
        if not any(values.values()):
            continue
        rows.append(WorkbookRow(row_number=offset, values=values))
    return WorkbookContent(rows=tuple(rows), headers=headers, file_sha256=digest)


def _find_header_row(rows: list[tuple[object, ...]]) -> int:
    required = {normalize_header(header) for header in REQUIRED_HEADERS}
    best_missing: set[str] = required
    for index, cells in enumerate(rows[:HEADER_SEARCH_ROWS]):
        present = {normalize_header(cell_text(cell)) for cell in cells}
        missing = required - present
        if not missing:
            return index
        if len(missing) < len(best_missing):
            best_missing = missing
    names = [header for header in REQUIRED_HEADERS if normalize_header(header) in best_missing]
    raise WorkbookReadError("Required headers not found: " + ", ".join(names) + ".")


def cell_text(value: object) -> str:
    """Cell value as text; whole floats lose their ``.0``; dates become ISO."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()
