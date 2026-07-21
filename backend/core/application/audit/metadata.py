from __future__ import annotations

from typing import Any


def changed_fields_metadata(*fields: str) -> dict[str, Any]:
    return {"changed_fields": list(fields)}


def role_change_metadata(*, previous_role: str, new_role: str) -> dict[str, Any]:
    return {
        "previous_role": previous_role,
        "new_role": new_role,
    }


def status_change_metadata(*, previous_status: str, new_status: str) -> dict[str, Any]:
    return {
        "previous_status": previous_status,
        "new_status": new_status,
    }
