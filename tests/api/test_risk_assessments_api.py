from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.entities.membership import Membership
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role
from backend.core.domain.value_objects.safety_enums import (
    HazardCategory,
    HazardSource,
    SafetyDirection,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryHazardRepository,
    InMemoryInvitationRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryRiskAssessmentRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from tests.api.contracts.assertions import assert_error_envelope
from tests.security.conftest import build_enforced_client


@pytest.fixture
def enforced_auth_settings() -> AppSettings:
    return AppSettings(
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


def _headers(organization_id: OrganizationId, token: str) -> dict[str, str]:
    return {
        ORGANIZATION_ID_HEADER: str(organization_id.value),
        "Authorization": f"Bearer {token}",
    }


def _build_client(settings: AppSettings, *, role: Role):
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    invitations = InMemoryInvitationRepository()
    hazards = InMemoryHazardRepository()
    risk_assessments = InMemoryRiskAssessmentRepository()
    audit_events = InMemoryAuditEventRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            organizations=organizations,
            memberships=memberships,
            invitations=invitations,
            hazards=hazards,
            risk_assessments=risk_assessments,
            audit_events=audit_events,
        )

    client, organization_id, access_token, user_id = build_enforced_client(
        settings,
        role=role,
    )
    now = datetime.now(UTC)
    organizations.add(
        Organization(
            id=organization_id,
            name="Authorization Organization",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    users.add(
        User(
            id=user_id,
            display_name="Safety Operator",
            email=f"operator-{uuid4()}@example.com",
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    stored = client.app.state.container.membership_store.get_membership(
        user_id,
        organization_id,
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
    hazard = Hazard.create(
        organization_id=organization_id,
        code="HZ-RA-1",
        title="Active hazard",
        description="",
        category=HazardCategory.PHYSICAL,
        safety_directions=(SafetyDirection.OCCUPATIONAL_SAFETY,),
        source=HazardSource.INSPECTION,
        identified_at=now,
        identified_by=user_id,
        created_at=now,
    ).activate(at=now, reviewed_by=user_id)
    hazards.add(hazard)
    client.app.state.container.uow_factory = uow_factory
    return (
        client,
        organization_id,
        access_token,
        user_id,
        hazard,
        risk_assessments,
        audit_events,
    )


def test_risk_assessment_lifecycle_and_supersede(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, risks, audits = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-assessments",
        headers=headers,
        json={
            "hazard_id": str(hazard.id.value),
            "code": "RA-100",
            "title": "Workplace assessment",
            "assessment_profile": "simple_5x5",
            "assessed_object": {
                "object_type": "workplace",
                "reference": "Shop-1",
            },
        },
    )
    assert created.status_code == 201
    assessment_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/risk-assessments/{assessment_id}",
        headers=headers,
        json={
            "expected_version": 1,
            "inherent_risk": {
                "probability": "possible",
                "severity": "major",
                "explanation": "Unguarded motion",
            },
            "residual_risk": {
                "probability": "unlikely",
                "severity": "moderate",
                "explanation": "After guarding",
            },
            "acceptance": {
                "decision": "accepted",
                "justification": "Controls reduce residual risk",
            },
            "controls": [
                {
                    "control_type": "engineering",
                    "description": "Install guard",
                    "implemented": True,
                    "effective": True,
                }
            ],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["inherent_risk"]["level"] == "high"
    assert updated.json()["version"] == 2

    approved = client.post(
        f"/api/v1/risk-assessments/{assessment_id}/approve",
        headers=headers,
        json={"expected_version": 2},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    second = client.post(
        "/api/v1/risk-assessments",
        headers=headers,
        json={
            "hazard_id": str(hazard.id.value),
            "code": "RA-101",
            "title": "Workplace assessment v2",
            "assessment_profile": "simple_5x5",
            "assessed_object": {
                "object_type": "workplace",
                "reference": "Shop-1",
            },
        },
    )
    assert second.status_code == 201
    second_id = second.json()["id"]
    client.patch(
        f"/api/v1/risk-assessments/{second_id}",
        headers=headers,
        json={
            "expected_version": 1,
            "inherent_risk": {"probability": 2, "severity": 2},
            "acceptance": {
                "decision": "accepted",
                "justification": "Updated controls",
            },
        },
    )
    approved2 = client.post(
        f"/api/v1/risk-assessments/{second_id}/approve",
        headers=headers,
        json={"expected_version": 2},
    )
    assert approved2.status_code == 200
    first = client.get(
        f"/api/v1/risk-assessments/{assessment_id}",
        headers=headers,
    )
    assert first.json()["status"] == "superseded"
    assert any(
        event.action.value.startswith("safety.risk.")
        for event in audits.snapshot().values()
    )
    assert len(risks.snapshot()) == 2


def test_member_cannot_approve_risk_assessment(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-assessments",
        headers=headers,
        json={
            "hazard_id": str(hazard.id.value),
            "code": "RA-200",
            "title": "Member assessment",
            "assessment_profile": "simple_3x3",
            "assessed_object": {
                "object_type": "equipment",
                "reference": "EQ-9",
            },
        },
    )
    assert created.status_code == 201
    approve = client.post(
        f"/api/v1/risk-assessments/{created.json()['id']}/approve",
        headers=headers,
        json={"expected_version": 1},
    )
    assert approve.status_code == 403


def test_cross_tenant_risk_assessment_is_masked(
    enforced_auth_settings: AppSettings,
) -> None:
    admin_client, org_a, token_a, _, hazard, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    created = admin_client.post(
        "/api/v1/risk-assessments",
        headers=_headers(org_a, token_a),
        json={
            "hazard_id": str(hazard.id.value),
            "code": "RA-300",
            "title": "Org A assessment",
            "assessment_profile": "simple_5x5",
            "assessed_object": {
                "object_type": "location",
                "reference": "Yard",
            },
        },
    )
    assessment_id = created.json()["id"]
    other_client, org_b, token_b, _, _, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    response = other_client.get(
        f"/api/v1/risk-assessments/{assessment_id}",
        headers=_headers(org_b, token_b),
    )
    assert response.status_code == 404
    assert_error_envelope(
        response,
        status_code=404,
        code="risk_assessment_not_found",
    )
