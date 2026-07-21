from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateOrganizationCommand:
    name: str
    is_active: bool = True
