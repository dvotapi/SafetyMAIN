from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotKeptOn,
    SlotObligationLevel,
)
from tests.fixtures.compliance_documents import FIXED_AT, make_actor


def make_section(
    *,
    organization_id: OrganizationId | None = None,
    code: str = "ТрБ",
    number: int = 10,
    title: str = "Транспортная безопасность",
    safety_domain: SafetyDomain = SafetyDomain.TRANSPORT_SECURITY,
    subsections: tuple[tuple[str, str], ...] = (
        ("01", "Оценка уязвимости"),
        ("02", "План обеспечения"),
    ),
) -> ShelfSection:
    section = ShelfSection.create(
        organization_id=organization_id or OrganizationId(value=uuid4()),
        code=code,
        number=number,
        title=title,
        safety_domain=safety_domain,
        created_at=FIXED_AT,
    )
    for number_part, subsection_title in subsections:
        section = section.add_subsection(
            code=f"{code}.{number_part}",
            title=subsection_title,
            at=FIXED_AT,
            expected_version=section.version,
        )
    return section


def make_slot(
    section: ShelfSection | None = None,
    *,
    code: str | None = None,
    created_by: UserId | None = None,
    curated_status: CuratedSlotStatus = CuratedSlotStatus.MISSING,
    obligation_level: SlotObligationLevel = SlotObligationLevel.MANDATORY,
    **kwargs: Any,
) -> ShelfSlot:
    section = section or make_section()
    defaults: dict[str, Any] = {
        "title": "План обеспечения транспортной безопасности",
        "short_title": "План ОТБ",
        "document_kind": "План",
        "kept_on": SlotKeptOn.ORGANIZATION,
    }
    if obligation_level is SlotObligationLevel.CONDITIONAL:
        defaults["applicability_condition"] = "При наличии ОТИ"
    return ShelfSlot.create(
        organization_id=section.organization_id,
        section=section,
        code=code or f"{section.subsections[0].code}.01",
        obligation_level=obligation_level,
        curated_status=curated_status,
        created_by=created_by or make_actor(),
        created_at=FIXED_AT,
        **{**defaults, **kwargs},
    )
