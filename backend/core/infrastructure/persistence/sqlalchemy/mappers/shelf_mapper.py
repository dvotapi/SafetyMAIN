from __future__ import annotations

from collections.abc import Sequence

from backend.core.domain.entities.shelf_section import ShelfSection, ShelfSubsection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
    ShelfSubsectionId,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    LegalBasisConfidence,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_slot_code import ShelfSlotCode
from backend.core.domain.value_objects.shelf_values import SlotExclusion, SlotLegalBasis
from backend.core.infrastructure.persistence.sqlalchemy.models.shelf_model import (
    ShelfSectionModel,
    ShelfSlotDocumentModel,
    ShelfSlotModel,
    ShelfSubsectionModel,
)


def section_to_model(section: ShelfSection) -> ShelfSectionModel:
    return ShelfSectionModel(
        id=section.id.value,
        organization_id=section.organization_id.value,
        code=section.code,
        number=section.number,
        title=section.title,
        safety_domain=section.safety_domain.value,
        created_at=section.created_at,
        updated_at=section.updated_at,
        version=section.version,
    )


def subsection_to_model(section: ShelfSection, subsection: ShelfSubsection) -> ShelfSubsectionModel:
    return ShelfSubsectionModel(
        id=subsection.id.value,
        organization_id=section.organization_id.value,
        section_id=section.id.value,
        code=subsection.code,
        title=subsection.title,
        position=subsection.position,
    )


def section_to_domain(
    model: ShelfSectionModel, subsections: Sequence[ShelfSubsectionModel]
) -> ShelfSection:
    return ShelfSection(
        id=ShelfSectionId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        code=model.code,
        number=model.number,
        title=model.title,
        safety_domain=SafetyDomain(model.safety_domain),
        subsections=tuple(
            ShelfSubsection(
                id=ShelfSubsectionId(value=row.id),
                code=row.code,
                title=row.title,
                position=row.position,
            )
            for row in sorted(subsections, key=lambda row: row.position)
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
        version=model.version,
    )


def slot_columns(slot: ShelfSlot) -> dict[str, object]:
    """Column values of a place (without links); used for insert and update."""
    exclusion = slot.exclusion
    return {
        "id": slot.id.value,
        "organization_id": slot.organization_id.value,
        "code": slot.code.value,
        "section_id": slot.section_id.value,
        "subsection_id": slot.subsection_id.value,
        "title": slot.title,
        "short_title": slot.short_title,
        "document_kind": slot.document_kind,
        "kept_on": slot.kept_on.value,
        "obligation_level": slot.obligation_level.value,
        "applicability_condition": slot.applicability_condition,
        "basis_regulation": slot.legal_basis.regulation,
        "basis_clause": slot.legal_basis.clause,
        "basis_quote": slot.legal_basis.quote,
        "basis_source_url": slot.legal_basis.source_url,
        "basis_confidence": slot.legal_basis.confidence.value,
        "review_cycle_text": slot.review_cycle_text,
        "review_period_months": slot.review_period_months,
        "curated_status": slot.curated_status.value,
        "document_type_code": slot.document_type_code,
        "proposed_document_type": slot.proposed_document_type,
        "responsible_text": slot.responsible_text,
        "legacy_location": slot.legacy_location,
        "notes": slot.notes,
        "package_code": slot.package_code,
        "legacy_code": slot.legacy_code,
        "exclusion_reason": None if exclusion is None else exclusion.reason.value,
        "exclusion_comment": None if exclusion is None else exclusion.comment,
        "exclusion_status_before": (
            None if exclusion is None else exclusion.status_before.value
        ),
        "excluded_by": None if exclusion is None else exclusion.excluded_by.value,
        "excluded_at": None if exclusion is None else exclusion.excluded_at,
        "import_fingerprint": slot.import_fingerprint,
        "last_imported_at": slot.last_imported_at,
        "created_at": slot.created_at,
        "created_by": slot.created_by.value,
        "updated_at": slot.updated_at,
        "updated_by": slot.updated_by.value,
        "version": slot.version,
    }


def slot_to_domain(
    model: ShelfSlotModel, links: Sequence[ShelfSlotDocumentModel]
) -> ShelfSlot:
    exclusion = None
    if model.exclusion_reason is not None:
        assert model.exclusion_comment is not None
        assert model.exclusion_status_before is not None
        assert model.excluded_by is not None and model.excluded_at is not None
        exclusion = SlotExclusion(
            reason=SlotExclusionReason(model.exclusion_reason),
            comment=model.exclusion_comment,
            status_before=CuratedSlotStatus(model.exclusion_status_before),
            excluded_by=UserId(value=model.excluded_by),
            excluded_at=model.excluded_at,
        )
    return ShelfSlot(
        id=ShelfSlotId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        code=ShelfSlotCode(value=model.code),
        section_id=ShelfSectionId(value=model.section_id),
        subsection_id=ShelfSubsectionId(value=model.subsection_id),
        title=model.title,
        short_title=model.short_title,
        document_kind=model.document_kind,
        kept_on=SlotKeptOn(model.kept_on),
        obligation_level=SlotObligationLevel(model.obligation_level),
        applicability_condition=model.applicability_condition,
        legal_basis=SlotLegalBasis(
            regulation=model.basis_regulation,
            clause=model.basis_clause,
            quote=model.basis_quote,
            source_url=model.basis_source_url,
            confidence=LegalBasisConfidence(model.basis_confidence),
        ),
        review_cycle_text=model.review_cycle_text,
        review_period_months=model.review_period_months,
        curated_status=CuratedSlotStatus(model.curated_status),
        document_type_code=model.document_type_code,
        proposed_document_type=model.proposed_document_type,
        responsible_text=model.responsible_text,
        legacy_location=model.legacy_location,
        notes=model.notes,
        package_code=model.package_code,
        legacy_code=model.legacy_code,
        exclusion=exclusion,
        linked_document_ids=tuple(
            ComplianceDocumentId(value=link.document_id)
            for link in sorted(links, key=lambda link: link.position)
        ),
        import_fingerprint=model.import_fingerprint,
        last_imported_at=model.last_imported_at,
        created_at=model.created_at,
        created_by=UserId(value=model.created_by),
        updated_at=model.updated_at,
        updated_by=UserId(value=model.updated_by),
        version=model.version,
    )
