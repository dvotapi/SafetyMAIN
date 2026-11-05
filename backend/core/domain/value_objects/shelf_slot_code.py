from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# Section prefixes are Cyrillic and may mix case (`ПожБ`); digits are ASCII only.
SHELF_SECTION_CODE_PATTERN = re.compile(r"^[А-ЯЁа-яё]{2,6}$")
SHELF_SUBSECTION_CODE_PATTERN = re.compile(r"^[А-ЯЁа-яё]{2,6}\.[0-9]{2}$")
SHELF_SLOT_CODE_PATTERN = re.compile(r"^[А-ЯЁа-яё]+\.[0-9]{2}\.[0-9]{2}$")


class ShelfSlotCode(BaseModel):
    """Permanent place code `SECTION.SS.NN`, e.g. `ВМ.10.01`."""

    model_config = ConfigDict(frozen=True)

    value: str

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            return {"value": data}
        return data

    @field_validator("value")
    @classmethod
    def require_pattern(cls, value: str) -> str:
        if not SHELF_SLOT_CODE_PATTERN.fullmatch(value):
            raise ValueError(
                "Shelf place code must look like SECTION.SS.NN (e.g. ВМ.10.01)."
            )
        return value

    @property
    def section_code(self) -> str:
        return self.value.split(".", 1)[0]

    @property
    def subsection_code(self) -> str:
        return self.value.rsplit(".", 1)[0]

    @property
    def sort_key(self) -> tuple[int, int]:
        """Subsection and place numbers, for ordering inside a section."""
        _, subsection, place = self.value.split(".")
        return int(subsection), int(place)

    def __str__(self) -> str:
        return self.value
