"""Workbook reader on synthetic .xlsx files (never the real workbook)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from backend.core.application.services.shelf_import_mapping import (
    H_CODE,
    H_PERIOD,
    H_STATUS,
)
from backend.core.infrastructure.importing.shelf_workbook_reader import (
    WorkbookReadError,
    read_shelf_workbook,
)
from tests.fixtures.shelf_workbook import HEADERS, place_row, write_workbook


def test_reads_rows_below_the_header_found_by_name(tmp_path: Path) -> None:
    path = write_workbook(
        tmp_path / "shelf.xlsx",
        [place_row("ТрБ.01.01"), {}, place_row("ТрБ.01.02", **{H_STATUS: "Есть"})],
        header_row=3,
    )

    content = read_shelf_workbook(path)

    assert [row.row_number for row in content.rows] == [4, 6]
    assert content.rows[0].values[H_CODE] == "ТрБ.01.01"
    assert content.rows[0].values[H_PERIOD] == "60"
    assert content.rows[1].values[H_STATUS] == "Есть"
    assert content.headers == HEADERS
    assert content.file_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()


def test_header_row_may_move_and_columns_may_be_reordered(tmp_path: Path) -> None:
    headers = tuple(reversed(HEADERS))
    path = write_workbook(tmp_path / "s.xlsx", [place_row()], headers=headers, header_row=6)

    content = read_shelf_workbook(path)

    assert content.rows[0].row_number == 7
    assert content.rows[0].values[H_CODE] == "ТрБ.01.01"


def test_missing_required_header_is_named(tmp_path: Path) -> None:
    headers = tuple(header for header in HEADERS if header != H_STATUS)
    path = write_workbook(tmp_path / "s.xlsx", [place_row()], headers=headers)

    with pytest.raises(WorkbookReadError, match="Статус"):
        read_shelf_workbook(path)


def test_missing_sheet_and_wrong_extension(tmp_path: Path) -> None:
    with pytest.raises(WorkbookReadError, match="Полка"):
        read_shelf_workbook(write_workbook(tmp_path / "s.xlsx", [], sheet="Лист1"))
    other = tmp_path / "s.csv"
    other.write_text("Код\n", encoding="utf-8")
    with pytest.raises(WorkbookReadError, match="xlsx"):
        read_shelf_workbook(other)
    with pytest.raises(WorkbookReadError, match="not found"):
        read_shelf_workbook(tmp_path / "absent.xlsx")
