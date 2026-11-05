"""In-memory enforced-auth client for the shelf API tests (synthetic data only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.membership import Membership
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryComplianceDocumentRepository,
    InMemoryDocumentTypeRepository,
    InMemoryHazardRepository,
    InMemoryInvitationRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryRiskAssessmentRepository,
    InMemoryRiskControlRepository,
    InMemoryShelfSectionRepository,
    InMemoryShelfSlotRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from tests.fixtures.compliance_documents import make_document_type
from tests.fixtures.shelf import make_section, make_slot
from tests.security.conftest import build_enforced_client

ENFORCED_SETTINGS = AppSettings(
    app_name="SafetyMAIN API",
    app_version="0.1.0",
    app_env="test",
    database_url=None,
    jwt_secret_key="test-secret-key-with-sufficient-length",
    jwt_algorithm="HS256",
    jwt_access_token_ttl_seconds=3600,
    jwt_refresh_token_ttl_seconds=604800,
    jwt_issuer="safetymain",
    auth_enforcement=True,
)


@dataclass
class ShelfClient:
    client: TestClient
    organization_id: OrganizationId
    user_id: UserId
    token: str
    users: InMemoryUserRepository
    document_types: InMemoryDocumentTypeRepository
    documents: InMemoryComplianceDocumentRepository
    sections: InMemoryShelfSectionRepository
    slots: InMemoryShelfSlotRepository
    audit_events: InMemoryAuditEventRepository
    document_type: DocumentType

    @property
    def headers(self) -> dict[str, str]:
        return {
            ORGANIZATION_ID_HEADER: str(self.organization_id.value),
            "Authorization": f"Bearer {self.token}",
        }

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.client.get(f"/api/v1/shelf{path}", headers=self.headers, **kwargs)

    def post(self, path: str, json: object) -> Any:
        return self.client.post(f"/api/v1/shelf{path}", headers=self.headers, json=json)

    def patch(self, path: str, json: object) -> Any:
        return self.client.patch(f"/api/v1/shelf{path}", headers=self.headers, json=json)

    def seed_section(self, **kwargs: Any) -> ShelfSection:
        section = make_section(organization_id=self.organization_id, **kwargs)
        self.sections.add(section)
        return section

    def seed_slot(self, section: ShelfSection, **kwargs: Any) -> ShelfSlot:
        slot = make_slot(section, created_by=self.user_id, **kwargs)
        self.slots.add(slot)
        return slot

    def events(self, action: str) -> list[AuditEvent]:
        return sorted(
            (
                event
                for event in self.audit_events.snapshot().values()
                if event.action.value == action
            ),
            key=lambda event: event.occurred_at,
        )


def build_shelf_client(*, role: Role | None = None) -> ShelfClient:
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    document_types = InMemoryDocumentTypeRepository()
    documents = InMemoryComplianceDocumentRepository()
    sections = InMemoryShelfSectionRepository()
    slots = InMemoryShelfSlotRepository()
    audit_events = InMemoryAuditEventRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            organizations=organizations,
            memberships=memberships,
            invitations=InMemoryInvitationRepository(),
            hazards=InMemoryHazardRepository(),
            risk_assessments=InMemoryRiskAssessmentRepository(),
            risk_controls=InMemoryRiskControlRepository(),
            document_types=document_types,
            compliance_documents=documents,
            shelf_sections=sections,
            shelf_slots=slots,
            audit_events=audit_events,
        )

    client, organization_id, token, user_id = build_enforced_client(
        ENFORCED_SETTINGS, role=role or Role.admin()
    )
    now = datetime.now(UTC)
    organizations.add(
        Organization(
            id=organization_id,
            name="Shelf Organization",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    users.add(
        User(
            id=user_id,
            display_name="Куратор Полки",
            email=f"curator-{uuid4()}@example.com",
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    stored = client.app.state.container.membership_store.get_membership(
        user_id, organization_id
    )
    assert stored is not None
    memberships.add(
        Membership(
            id=stored.id,
            user_id=stored.user_id,
            organization_id=stored.organization_id,
            status=stored.status,
            role=stored.role,
            joined_at=stored.joined_at or now,
            updated_at=now,
            revoked_at=stored.revoked_at,
        )
    )
    client.app.state.container.uow_factory = uow_factory
    document_type = make_document_type(
        organization_id=organization_id,
        code="transport_plan",
        safety_domain=SafetyDomain.TRANSPORT_SECURITY,
    )
    document_types.add(document_type)
    return ShelfClient(
        client=client,
        organization_id=organization_id,
        user_id=user_id,
        token=token,
        users=users,
        document_types=document_types,
        documents=documents,
        sections=sections,
        slots=slots,
        audit_events=audit_events,
        document_type=document_type,
    )
