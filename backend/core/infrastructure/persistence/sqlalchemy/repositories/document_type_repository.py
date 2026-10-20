from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import DuplicateDocumentTypeCode
from backend.core.domain.repositories.document_type_repository import (
    DocumentTypeRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import DocumentTypeId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.document_type_mapper import (
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.document_type_model import (
    DocumentTypeModel,
)


class SQLAlchemyDocumentTypeRepository(DocumentTypeRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document_type: DocumentType) -> None:
        if self.get_by_code(document_type.organization_id, document_type.code) is not None:
            raise DuplicateDocumentTypeCode(
                organization_id=document_type.organization_id,
                code=document_type.code,
            )
        self._session.add(to_model(document_type))
        try:
            self._session.flush()
        except IntegrityError as error:
            if "uq_document_types_organization_id_code" in str(error.orig):
                raise DuplicateDocumentTypeCode(
                    organization_id=document_type.organization_id,
                    code=document_type.code,
                ) from error
            raise

    def get(
        self,
        organization_id: OrganizationId,
        document_type_id: DocumentTypeId,
    ) -> DocumentType | None:
        model = self._session.scalar(
            select(DocumentTypeModel).where(
                DocumentTypeModel.id == document_type_id.value,
                DocumentTypeModel.organization_id == organization_id.value,
            )
        )
        return None if model is None else to_domain(model)

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: str,
    ) -> DocumentType | None:
        model = self._session.scalar(
            select(DocumentTypeModel).where(
                DocumentTypeModel.organization_id == organization_id.value,
                DocumentTypeModel.code == code,
            )
        )
        return None if model is None else to_domain(model)

    def list(
        self,
        organization_id: OrganizationId,
        *,
        include_inactive: bool = False,
    ) -> tuple[DocumentType, ...]:
        statement = select(DocumentTypeModel).where(
            DocumentTypeModel.organization_id == organization_id.value
        )
        if not include_inactive:
            statement = statement.where(DocumentTypeModel.is_active.is_(True))
        statement = statement.order_by(DocumentTypeModel.code)
        models = self._session.scalars(statement).all()
        return tuple(to_domain(model) for model in models)
