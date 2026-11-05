from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.repositories.shelf_section_repository import (
    ShelfSectionRepositoryContract,
)
from backend.core.domain.repositories.shelf_slot_repository import (
    ShelfSlotRepositoryContract,
)
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.infrastructure.persistence.sqlalchemy.mappers.compliance_document_mapper import (
    to_model as document_to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.compliance_document_model import (
    ComplianceDocumentModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.shelf_model import (
    ShelfSectionModel,
    ShelfSubsectionModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.document_type_repository import (
    SQLAlchemyDocumentTypeRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.shelf_section_repository import (
    SQLAlchemyShelfSectionRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.shelf_slot_repository import (
    SQLAlchemyShelfSlotRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_shelf_section_repository_contracts import (
    ShelfSectionRepositoryContractSuite,
)
from tests.contracts.test_shelf_slot_repository_contracts import (
    ShelfSlotRepositoryContractSuite,
)
from tests.fixtures.compliance_documents import make_document_type

pytest_plugins = ("tests.infrastructure.db_fixtures",)


def ensure_shelf_slot_related(session: Session, slot: ShelfSlot) -> None:
    """Seed the rows a place references: organization, users, section, documents."""
    ensure_organization(session, slot.organization_id)
    for user_id in (slot.created_by, slot.updated_by):
        ensure_user(session, user_id)
    if slot.exclusion is not None:
        ensure_user(session, slot.exclusion.excluded_by)

    if session.get(ShelfSectionModel, slot.section_id.value) is None:
        top = session.scalar(
            select(func.max(ShelfSectionModel.number)).where(
                ShelfSectionModel.organization_id == slot.organization_id.value
            )
        )
        now = datetime.now(UTC)
        session.add(
            ShelfSectionModel(
                id=slot.section_id.value,
                organization_id=slot.organization_id.value,
                code=slot.code.section_code,
                number=(top or 0) + 1,
                title=f"Synthetic {slot.code.section_code}",
                safety_domain=SafetyDomain.OCCUPATIONAL.value,
                created_at=now,
                updated_at=now,
                version=1,
            )
        )
        session.flush()
    if session.get(ShelfSubsectionModel, slot.subsection_id.value) is None:
        top = session.scalar(
            select(func.max(ShelfSubsectionModel.position)).where(
                ShelfSubsectionModel.section_id == slot.section_id.value
            )
        )
        session.add(
            ShelfSubsectionModel(
                id=slot.subsection_id.value,
                organization_id=slot.organization_id.value,
                section_id=slot.section_id.value,
                code=slot.code.subsection_code,
                title="Synthetic",
                position=0 if top is None else top + 1,
            )
        )
        session.flush()

    for document_id in slot.linked_document_ids:
        if session.get(ComplianceDocumentModel, document_id.value) is not None:
            continue
        types = SQLAlchemyDocumentTypeRepository(session)
        document_type = types.get_by_code(slot.organization_id, "shelf-stub")
        if document_type is None:
            document_type = make_document_type(
                organization_id=slot.organization_id, code="shelf-stub"
            )
            types.add(document_type)
            session.flush()
        stub = ComplianceDocument.create(
            organization_id=slot.organization_id,
            document_type=document_type,
            code=f"stub-{document_id.value.hex[:8]}",
            title="Stub",
            created_by=slot.created_by,
            created_at=slot.created_at,
            document_id=document_id,
        )
        session.add(document_to_model(stub))
        session.flush()


class _SeedingShelfSlotRepository(SQLAlchemyShelfSlotRepository):
    def add(self, slot: ShelfSlot) -> None:
        ensure_shelf_slot_related(self._session, slot)
        super().add(slot)

    def save(self, slot: ShelfSlot, *, expected_version: int) -> None:
        ensure_shelf_slot_related(self._session, slot)
        super().save(slot, expected_version=expected_version)


class _SeedingShelfSectionRepository(SQLAlchemyShelfSectionRepository):
    def add(self, section: ShelfSection) -> None:
        ensure_organization(self._session, section.organization_id)
        super().add(section)


@pytest.mark.db
class TestSQLAlchemyShelfSectionRepositoryContract(ShelfSectionRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> ShelfSectionRepositoryContract:
        return _SeedingShelfSectionRepository(sqlalchemy_session)


@pytest.mark.db
class TestSQLAlchemyShelfSlotRepositoryContract(ShelfSlotRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> ShelfSlotRepositoryContract:
        return _SeedingShelfSlotRepository(sqlalchemy_session)
