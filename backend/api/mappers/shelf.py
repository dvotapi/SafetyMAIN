"""Map shelf views (application layer) to API DTOs; no calculation happens here."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from backend.api.schemas.shelf import (
    DevelopShelfSlotResponse,
    ShelfCurrentDocumentResponse,
    ShelfDocumentFileResponse,
    ShelfDocumentRefResponse,
    ShelfEditionResponse,
    ShelfGroupCountsResponse,
    ShelfOverviewResponse,
    ShelfSectionRefResponse,
    ShelfSectionSlotsResponse,
    ShelfSectionSummaryResponse,
    ShelfSlotDetailResponse,
    ShelfSlotExclusionResponse,
    ShelfSlotListResponse,
    ShelfSlotSummaryResponse,
    ShelfStripItemResponse,
    ShelfSubsectionSlotsResponse,
    ShelfTotalsResponse,
    SlotLegalBasisPayload,
    UpdateShelfSlotRequest,
)
from backend.core.application.handlers.shelf import (
    DevelopShelfSlotResult,
    ShelfOverviewView,
    ShelfSectionSlotsView,
    ShelfSlotDetailView,
    ShelfSlotView,
)
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentFile,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    LegalBasisConfidence,
    ShelfStatusGroup,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_values import SlotLegalBasis

_ENUM_FIELDS: dict[str, Any] = {
    "kept_on": SlotKeptOn,
    "obligation_level": SlotObligationLevel,
    "curated_status": CuratedSlotStatus,
}
def to_legal_basis(payload: SlotLegalBasisPayload | None) -> SlotLegalBasis | None:
    if payload is None:
        return None
    return SlotLegalBasis(
        regulation=payload.regulation,
        clause=payload.clause,
        quote=payload.quote,
        source_url=payload.source_url,
        confidence=LegalBasisConfidence(payload.confidence),
    )


def update_changes(request: UpdateShelfSlotRequest) -> dict[str, Any]:
    """Curated fields sent in the PATCH body, converted to domain values.

    ``null`` clears a nullable field; on a required one the domain rejects it.
    """
    changes: dict[str, Any] = {}
    for name in sorted(request.model_fields_set - {"version"}):
        value = getattr(request, name)
        if name == "legal_basis":
            changes[name] = to_legal_basis(value) or SlotLegalBasis()
        elif name in _ENUM_FIELDS and value is not None:
            changes[name] = _ENUM_FIELDS[name](value)
        else:
            changes[name] = value
    return changes


def _counts(by_group: Mapping[ShelfStatusGroup, int]) -> ShelfGroupCountsResponse:
    return ShelfGroupCountsResponse(
        **{group.value: by_group.get(group, 0) for group in ShelfStatusGroup}
    )


def to_overview_response(view: ShelfOverviewView) -> ShelfOverviewResponse:
    return ShelfOverviewResponse(
        sections=[
            ShelfSectionSummaryResponse(
                code=item.section.code,
                number=item.section.number,
                title=item.section.title,
                safety_domain=item.section.safety_domain.value,
                total=item.summary.total,
                mandatory_total=item.summary.mandatory_total,
                by_group=_counts(item.summary.by_group),
                readiness_percent=item.summary.readiness_percent,
                strip=[
                    ShelfStripItemResponse(
                        code=place.slot.code.value, group=place.evaluation.group.value
                    )
                    for place in item.strip
                ],
            )
            for item in view.sections
        ],
        totals=ShelfTotalsResponse(
            places=view.totals.total,
            excluded=view.totals.by_group.get(ShelfStatusGroup.EXCLUDED, 0),
            by_group=_counts(view.totals.by_group),
            readiness_percent=view.totals.readiness_percent,
        ),
        evaluated_at=view.evaluated_at,
    )


def _summary_fields(view: ShelfSlotView | ShelfSlotDetailView) -> dict[str, Any]:
    slot = view.slot
    return {
        "id": slot.id.value,
        "code": slot.code.value,
        "subsection_code": slot.code.subsection_code,
        "short_title": slot.short_title,
        "title": slot.title,
        "document_kind": slot.document_kind,
        "kept_on": slot.kept_on.value,
        "obligation_level": slot.obligation_level.value,
        "effective_status": view.evaluation.effective_status.value,
        "group": view.evaluation.group.value,
        "has_acknowledgement_gap": False,
    }


def to_slot_summary_response(view: ShelfSlotView) -> ShelfSlotSummaryResponse:
    return ShelfSlotSummaryResponse(**_summary_fields(view))


def to_slot_list_response(views: Iterable[ShelfSlotView]) -> ShelfSlotListResponse:
    return ShelfSlotListResponse(items=[to_slot_summary_response(view) for view in views])


def to_section_slots_response(view: ShelfSectionSlotsView) -> ShelfSectionSlotsResponse:
    return ShelfSectionSlotsResponse(
        section=ShelfSectionRefResponse(
            code=view.section.code, number=view.section.number, title=view.section.title
        ),
        subsections=[
            ShelfSubsectionSlotsResponse(
                code=item.subsection.code,
                title=item.subsection.title,
                slots=[to_slot_summary_response(place) for place in item.slots],
            )
            for item in view.subsections
        ],
    )


def _file(file: DocumentFile | None) -> ShelfDocumentFileResponse | None:
    if file is None:
        return None
    return ShelfDocumentFileResponse(
        file_id=file.id.value,
        content_type=file.content_type,
        size_bytes=file.size_bytes,
        uploaded_at=file.uploaded_at,
    )


def _current_document(
    document: ComplianceDocument | None, approved_by: ComplianceDocument | None
) -> ShelfCurrentDocumentResponse | None:
    if document is None:
        return None
    return ShelfCurrentDocumentResponse(
        id=document.id.value,
        code=document.code,
        title=document.title,
        status=document.status.value,
        effective_from=document.effective_from,
        next_review_at=document.next_review_at,
        approved_by_order=(
            ShelfDocumentRefResponse(code=approved_by.code, title=approved_by.title)
            if approved_by is not None
            else None
        ),
        signed_scan=None,
        working_file=_file(document.current_file),
    )


def _legal_basis(slot: ShelfSlot) -> SlotLegalBasisPayload:
    basis = slot.legal_basis
    return SlotLegalBasisPayload(
        regulation=basis.regulation,
        clause=basis.clause,
        quote=basis.quote,
        source_url=basis.source_url,
        confidence=basis.confidence.value,
    )


def to_slot_detail_response(view: ShelfSlotDetailView) -> ShelfSlotDetailResponse:
    slot = view.slot
    exclusion = slot.exclusion
    return ShelfSlotDetailResponse(
        **_summary_fields(view),
        section_code=slot.code.section_code,
        legal_basis=_legal_basis(slot),
        applicability_condition=slot.applicability_condition,
        review_cycle_text=slot.review_cycle_text,
        review_period_months=slot.review_period_months,
        review_date=view.evaluation.review_date,
        curated_status=slot.curated_status.value,
        document_type_code=slot.document_type_code,
        proposed_document_type=slot.proposed_document_type,
        responsible_text=slot.responsible_text,
        legacy_location=slot.legacy_location,
        notes=slot.notes,
        package_code=slot.package_code,
        legacy_code=slot.legacy_code,
        exclusion=(
            ShelfSlotExclusionResponse(
                reason=exclusion.reason.value,
                comment=exclusion.comment,
                excluded_by_name=view.excluded_by_name or "",
                excluded_at=exclusion.excluded_at,
            )
            if exclusion is not None
            else None
        ),
        current_document=_current_document(view.current_document, view.approved_by_order),
        editions=[
            ShelfEditionResponse(
                id=document.id.value,
                code=document.code,
                status=document.status.value,
                effective_from=document.effective_from,
            )
            for document in view.editions
        ],
        available_actions=[action.value for action in view.actions.all],
        primary_action=view.actions.primary.value if view.actions.primary else None,
        acknowledgement=None,
        version=slot.version,
    )


def to_develop_response(result: DevelopShelfSlotResult) -> DevelopShelfSlotResponse:
    return DevelopShelfSlotResponse(
        document_id=result.document.id.value, slot=to_slot_detail_response(result.slot)
    )
