from __future__ import annotations

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.domain.value_objects.safety_ids import DocumentTypeId
from backend.core.infrastructure.persistence.sqlalchemy.models.document_type_model import (
    DocumentTypeModel,
)


def to_model(document_type: DocumentType) -> DocumentTypeModel:
    return DocumentTypeModel(
        id=document_type.id.value,
        organization_id=document_type.organization_id.value,
        code=document_type.code,
        title_ru=document_type.title_ru,
        safety_domain=document_type.safety_domain.value,
        subject_kind=document_type.subject_kind.value,
        review_period_months=document_type.review_period_months,
        validity_months=document_type.validity_months,
        periodicity_months=document_type.periodicity_months,
        warning_thresholds_days=list(document_type.warning_thresholds_days),
        requires_acknowledgement=document_type.requires_acknowledgement,
        requires_approval_order=document_type.requires_approval_order,
        legal_basis=document_type.legal_basis,
        legal_basis_reference=document_type.legal_basis_reference,
        is_active=document_type.is_active,
        created_at=document_type.created_at,
        updated_at=document_type.updated_at,
    )


def apply_to_model(model: DocumentTypeModel, document_type: DocumentType) -> None:
    mapped = to_model(document_type)
    for column in DocumentTypeModel.__table__.columns:
        if column.name == "id":
            continue
        setattr(model, column.name, getattr(mapped, column.name))


def to_domain(model: DocumentTypeModel) -> DocumentType:
    return DocumentType(
        id=DocumentTypeId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        code=model.code,
        title_ru=model.title_ru,
        safety_domain=SafetyDomain(model.safety_domain),
        subject_kind=DocumentSubjectKind(model.subject_kind),
        review_period_months=model.review_period_months,
        validity_months=model.validity_months,
        periodicity_months=model.periodicity_months,
        warning_thresholds_days=tuple(model.warning_thresholds_days),
        requires_acknowledgement=model.requires_acknowledgement,
        requires_approval_order=model.requires_approval_order,
        legal_basis=model.legal_basis,
        legal_basis_reference=model.legal_basis_reference,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
