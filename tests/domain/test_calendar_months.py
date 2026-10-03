from __future__ import annotations

from datetime import date

import pytest

from backend.core.domain.services.calendar_months import add_months


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (date(2026, 3, 15), 0, date(2026, 3, 15)),
        (date(2026, 3, 15), 1, date(2026, 4, 15)),
        (date(2026, 11, 30), 2, date(2027, 1, 30)),
        (date(2026, 1, 31), 60, date(2031, 1, 31)),
        (date(2026, 12, 1), 12, date(2027, 12, 1)),
    ],
)
def test_add_months_keeps_day_of_month(start: date, months: int, expected: date) -> None:
    assert add_months(start, months) == expected


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (date(2024, 1, 31), 1, date(2024, 2, 29)),
        (date(2023, 1, 31), 1, date(2023, 2, 28)),
        (date(2024, 2, 29), 12, date(2025, 2, 28)),
        (date(2026, 3, 31), 1, date(2026, 4, 30)),
        (date(2026, 8, 31), 6, date(2027, 2, 28)),
    ],
)
def test_add_months_clamps_to_last_day_of_target_month(
    start: date, months: int, expected: date
) -> None:
    assert add_months(start, months) == expected
