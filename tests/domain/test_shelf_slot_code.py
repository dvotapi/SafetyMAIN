from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.core.domain.value_objects.shelf_slot_code import ShelfSlotCode


@pytest.mark.parametrize("code", ["ТрБ.02.02", "ВМ.10.01", "ПожБ.01.10", "ДОПОГ.03.07"])
def test_valid_codes(code: str) -> None:
    assert ShelfSlotCode(value=code).value == code


@pytest.mark.parametrize(
    "code",
    ["ТрБ.2.02", "ТрБ.02", "TrB.02.02", "ТрБ.02.02.01", "ТрБ.٠٢.02", " ТрБ.02.02", ""],
)
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValidationError):
        ShelfSlotCode(value=code)


def test_code_parts() -> None:
    code = ShelfSlotCode(value="ПожБ.03.12")
    assert code.section_code == "ПожБ"
    assert code.subsection_code == "ПожБ.03"
    assert code.sort_key == (3, 12)
    assert str(code) == "ПожБ.03.12"
