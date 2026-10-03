from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import DuplicateDocumentTypeCode
from backend.core.domain.repositories.document_type_repository import (
    DocumentTypeRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.infrastructure.persistence.in_memory.document_type_repository import (
    InMemoryDocumentTypeRepository,
)
from tests.fixtures.compliance_documents import FIXED_AT, make_document_type


class DocumentTypeRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> DocumentTypeRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_organization_isolation(
        self, repository: DocumentTypeRepositoryContract
    ) -> None:
        document_type = make_document_type()
        repository.add(document_type)

        assert repository.get(document_type.organization_id, document_type.id) == document_type
        assert repository.get(OrganizationId(value=uuid4()), document_type.id) is None

    def test_round_trip_preserves_all_fields(
        self, repository: DocumentTypeRepositoryContract
    ) -> None:
        document_type = DocumentType.create(
            organization_id=OrganizationId(value=uuid4()),
            code="ot_briefing_repeated",
            title_ru="Повторный инструктаж по охране труда",
            safety_domain=SafetyDomain.OCCUPATIONAL,
            subject_kind=DocumentSubjectKind.EMPLOYEE,
            periodicity_months=6,
            warning_thresholds_days=(14, 7),
            requires_acknowledgement=True,
            requires_approval_order=True,
            legal_basis="Порядок обучения по охране труда",
            legal_basis_reference="ПП РФ № 2464",
            is_active=False,
            created_at=FIXED_AT,
        )
        repository.add(document_type)

        assert repository.get(document_type.organization_id, document_type.id) == document_type

    def test_code_is_unique_per_organization(
        self, repository: DocumentTypeRepositoryContract
    ) -> None:
        first = make_document_type(code="order")
        repository.add(first)

        with pytest.raises(DuplicateDocumentTypeCode):
            repository.add(
                make_document_type(organization_id=first.organization_id, code="order")
            )
        repository.add(make_document_type(code="order"))

    def test_get_by_code_is_organization_scoped(
        self, repository: DocumentTypeRepositoryContract
    ) -> None:
        document_type = make_document_type(code="emergency_plan")
        repository.add(document_type)

        assert (
            repository.get_by_code(document_type.organization_id, "emergency_plan")
            == document_type
        )
        assert repository.get_by_code(document_type.organization_id, "order") is None
        assert repository.get_by_code(OrganizationId(value=uuid4()), "emergency_plan") is None

    def test_list_is_scoped_sorted_by_code_and_hides_inactive_by_default(
        self, repository: DocumentTypeRepositoryContract
    ) -> None:
        organization_id = OrganizationId(value=uuid4())
        regulation = make_document_type(organization_id=organization_id, code="regulation_suot")
        order = make_document_type(organization_id=organization_id, code="order")
        retired = make_document_type(
            organization_id=organization_id, code="iot_work_type", is_active=False
        )
        for document_type in (regulation, order, retired, make_document_type(code="foreign")):
            repository.add(document_type)

        assert repository.list(organization_id) == (order, regulation)
        assert repository.list(organization_id, include_inactive=True) == (
            retired,
            order,
            regulation,
        )


class TestInMemoryDocumentTypeRepository(DocumentTypeRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> DocumentTypeRepositoryContract:
        return InMemoryDocumentTypeRepository()
