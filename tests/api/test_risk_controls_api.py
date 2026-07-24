from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

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
from backend.core.domain.value_objects.safety_ids import RiskAssessmentId, RiskControlId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryHazardRepository,
    InMemoryInvitationRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryRiskAssessmentRepository,
    InMemoryRiskControlRepository,
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
    risk_controls = InMemoryRiskControlRepository()
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
            risk_controls=risk_controls,
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
        code=f"HZ-RC-{uuid4().hex[:6]}",
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
        risk_controls,
        audit_events,
    )


def _create_payload(*, code: str = "RC-API-1", hazard_id: str | None = None) -> dict:
    return {
        "code": code,
        "title": "API Guard",
        "description": "Engineering guard from API",
        "hierarchy_level": "engineering",
        "control_nature": "preventive",
        "source": {"source_type": "management_decision"},
        "scope": [{"scope_type": "workplace", "reference": "Bay-1"}],
        "hazard_id": hazard_id,
        "owner": {
            "owner_type": "user",
            "owner_reference": "owner-api",
            "display_name_snapshot": "API Owner",
        },
        "verification_method_requirement": "Walkdown",
        "extension_data": {"profile": "default"},
    }


def test_risk_control_full_lifecycle_workflow(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, _, controls, audits = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-controls",
        headers=headers,
        json=_create_payload(hazard_id=str(hazard.id.value)),
    )
    assert created.status_code == 201
    body = created.json()
    control_id = body["id"]
    assert body["lifecycle_status"] == "draft"
    assert body["version"] == 1

    got = client.get(f"/api/v1/risk-controls/{control_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["code"] == "RC-API-1"

    updated = client.patch(
        f"/api/v1/risk-controls/{control_id}",
        headers=headers,
        json={"expected_version": 1, "title": "API Guard Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "API Guard Updated"
    assert updated.json()["version"] == 2

    assigned = client.post(
        f"/api/v1/risk-controls/{control_id}/assign-owner",
        headers=headers,
        json={
            "expected_version": 2,
            "owner": {
                "owner_type": "role",
                "owner_reference": "site-safety",
                "display_name_snapshot": "Site Safety",
            },
            "reason": "handover",
        },
    )
    assert assigned.status_code == 200
    assert assigned.json()["owner"]["owner_reference"] == "site-safety"

    planned = client.post(
        f"/api/v1/risk-controls/{control_id}/plan",
        headers=headers,
        json={
            "expected_version": 3,
            "implementation": {
                "target_completion_date": (
                    datetime.now(UTC) + timedelta(days=10)
                ).isoformat(),
                "implementation_method": "Install",
            },
            "verification_method_requirement": "Function test",
        },
    )
    assert planned.status_code == 200
    assert planned.json()["lifecycle_status"] == "planned"

    started = client.post(
        f"/api/v1/risk-controls/{control_id}/start-implementation",
        headers=headers,
        json={"expected_version": 4},
    )
    assert started.status_code == 200
    assert started.json()["lifecycle_status"] == "in_implementation"

    progress = client.post(
        f"/api/v1/risk-controls/{control_id}/progress",
        headers=headers,
        json={"expected_version": 5, "progress": 50, "summary": "Halfway"},
    )
    assert progress.status_code == 200
    assert progress.json()["implementation"]["progress"] == 50

    evidence = client.post(
        f"/api/v1/risk-controls/{control_id}/evidence",
        headers=headers,
        json={
            "expected_version": 6,
            "evidence_type": "photo",
            "external_reference": "doc://api-1",
            "title": "Photo evidence",
        },
    )
    assert evidence.status_code == 200
    assert len(evidence.json()["evidence"]) == 1

    completed = client.post(
        f"/api/v1/risk-controls/{control_id}/complete-implementation",
        headers=headers,
        json={"expected_version": 7, "summary": "Installed"},
    )
    assert completed.status_code == 200
    assert completed.json()["lifecycle_status"] == "implemented"

    verified = client.post(
        f"/api/v1/risk-controls/{control_id}/verifications",
        headers=headers,
        json={
            "expected_version": 8,
            "method": "Walkdown",
            "result": "effective",
            "evidence_refs": ["doc://api-1"],
            "next_review_date": (datetime.now(UTC) + timedelta(days=180)).isoformat(),
        },
    )
    assert verified.status_code == 200
    assert verified.json()["lifecycle_status"] == "verified_effective"
    assert verified.json()["latest_effectiveness_result"] == "effective"

    scheduled = client.post(
        f"/api/v1/risk-controls/{control_id}/schedule-review",
        headers=headers,
        json={
            "expected_version": 9,
            "schedule": {
                "review_required": True,
                "review_frequency_days": 90,
                "next_review_date": (
                    datetime.now(UTC) + timedelta(days=90)
                ).isoformat(),
            },
        },
    )
    assert scheduled.status_code == 200
    assert scheduled.json()["review_schedule"]["review_frequency_days"] == 90

    listed = client.get(
        "/api/v1/risk-controls",
        headers=headers,
        params={"status": "verified_effective", "search": "Guard"},
    )
    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] >= 1

    assert any(
        event.action.value.startswith("safety.risk_control.")
        for event in audits.snapshot().values()
    )
    assert controls.get(
        org,
        RiskControlId(value=UUID(control_id)),
    ) is not None


def test_risk_control_no_delete_route(enforced_auth_settings: AppSettings) -> None:
    client, org, token, _, hazard, *_ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-controls",
        headers=headers,
        json=_create_payload(code="RC-DEL", hazard_id=str(hazard.id.value)),
    )
    control_id = created.json()["id"]
    # Platform maps unsupported methods through a generic HTTP handler; assert the
    # route is absent from OpenAPI and that DELETE is not a successful business op.
    schema = client.get("/openapi.json").json()
    assert "delete" not in schema["paths"]["/api/v1/risk-controls/{control_id}"]
    deleted = client.delete(f"/api/v1/risk-controls/{control_id}", headers=headers)
    assert deleted.status_code >= 400
    assert client.get(
        f"/api/v1/risk-controls/{control_id}",
        headers=headers,
    ).status_code == 200


def test_risk_control_cross_tenant_masked(
    enforced_auth_settings: AppSettings,
) -> None:
    admin_client, org_a, token_a, _, hazard, *_ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    created = admin_client.post(
        "/api/v1/risk-controls",
        headers=_headers(org_a, token_a),
        json=_create_payload(code="RC-TENANT", hazard_id=str(hazard.id.value)),
    )
    control_id = created.json()["id"]
    other_client, org_b, token_b, *_ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers_b = _headers(org_b, token_b)
    assert (
        other_client.get(
            f"/api/v1/risk-controls/{control_id}",
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        other_client.patch(
            f"/api/v1/risk-controls/{control_id}",
            headers=headers_b,
            json={"expected_version": 1, "title": "x"},
        ).status_code
        == 404
    )
    assert (
        other_client.post(
            f"/api/v1/risk-controls/{control_id}/plan",
            headers=headers_b,
            json={
                "expected_version": 1,
                "implementation": {
                    "target_completion_date": datetime.now(UTC).isoformat()
                },
            },
        ).status_code
        == 404
    )


def test_risk_control_stale_version_conflict(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, *_ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-controls",
        headers=headers,
        json=_create_payload(code="RC-VER", hazard_id=str(hazard.id.value)),
    )
    control_id = created.json()["id"]
    client.patch(
        f"/api/v1/risk-controls/{control_id}",
        headers=headers,
        json={"expected_version": 1, "title": "First"},
    )
    stale = client.patch(
        f"/api/v1/risk-controls/{control_id}",
        headers=headers,
        json={"expected_version": 1, "title": "Stale"},
    )
    assert stale.status_code == 409
    assert_error_envelope(
        stale,
        status_code=409,
        code="risk_control_version_conflict",
    )


def test_member_cannot_verify_risk_control(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, *_ = _build_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-controls",
        headers=headers,
        json=_create_payload(code="RC-PERM", hazard_id=str(hazard.id.value)),
    )
    assert created.status_code == 201
    control_id = created.json()["id"]
    # Member can plan/update but not verify
    client.post(
        f"/api/v1/risk-controls/{control_id}/plan",
        headers=headers,
        json={
            "expected_version": 1,
            "implementation": {
                "target_completion_date": (
                    datetime.now(UTC) + timedelta(days=5)
                ).isoformat()
            },
        },
    )
    verify = client.post(
        f"/api/v1/risk-controls/{control_id}/verifications",
        headers=headers,
        json={
            "expected_version": 2,
            "method": "x",
            "result": "effective",
            "evidence_refs": ["a"],
            "next_review_date": datetime.now(UTC).isoformat(),
        },
    )
    assert verify.status_code == 403


def test_materialize_controls_and_duplicate(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, assessments, _, audits = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-assessments",
        headers=headers,
        json={
            "hazard_id": str(hazard.id.value),
            "code": "RA-MAT-1",
            "title": "Assessment with controls",
            "assessment_profile": "simple_5x5",
            "assessed_object": {
                "object_type": "workplace",
                "reference": "Shop",
            },
        },
    )
    assessment_id = created.json()["id"]
    updated = client.patch(
        f"/api/v1/risk-assessments/{assessment_id}",
        headers=headers,
        json={
            "expected_version": 1,
            "inherent_risk": {"probability": 2, "severity": 2},
            "acceptance": {
                "decision": "accepted",
                "justification": "ok",
            },
            "controls": [
                {
                    "control_type": "engineering",
                    "description": "Install guard",
                },
                {
                    "control_type": "ppe",
                    "description": "Safety glasses",
                },
            ],
        },
    )
    assert updated.status_code == 200
    approved = client.post(
        f"/api/v1/risk-assessments/{assessment_id}/approve",
        headers=headers,
        json={"expected_version": 2},
    )
    assert approved.status_code == 200
    before = assessments.get(
        org,
        RiskAssessmentId(value=UUID(assessment_id)),
    )
    assert before is not None
    assessment_version = before.version

    materialized = client.post(
        f"/api/v1/risk-assessments/{assessment_id}/materialize-controls",
        headers=headers,
        json={},
    )
    assert materialized.status_code == 200
    items = materialized.json()["items"]
    assert len(items) == 2
    assert all(item["source"]["source_control_reference"] for item in items)
    after = assessments.get(
        org,
        RiskAssessmentId(value=UUID(assessment_id)),
    )
    assert after is not None
    assert after.version == assessment_version
    assert after.controls == before.controls

    duplicate = client.post(
        f"/api/v1/risk-assessments/{assessment_id}/materialize-controls",
        headers=headers,
        json={},
    )
    assert duplicate.status_code == 409
    assert_error_envelope(
        duplicate,
        status_code=409,
        code="risk_control_already_materialized",
    )
    assert any(
        event.action.value == "safety.risk_control.materialized"
        for event in audits.snapshot().values()
    )


def test_verification_result_variants(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, *_ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)

    def _ready(code: str) -> tuple[str, int]:
        created = client.post(
            "/api/v1/risk-controls",
            headers=headers,
            json=_create_payload(code=code, hazard_id=str(hazard.id.value)),
        )
        control_id = created.json()["id"]
        client.post(
            f"/api/v1/risk-controls/{control_id}/plan",
            headers=headers,
            json={
                "expected_version": 1,
                "implementation": {
                    "target_completion_date": datetime.now(UTC).isoformat()
                },
            },
        )
        client.post(
            f"/api/v1/risk-controls/{control_id}/start-implementation",
            headers=headers,
            json={"expected_version": 2},
        )
        client.post(
            f"/api/v1/risk-controls/{control_id}/evidence",
            headers=headers,
            json={
                "expected_version": 3,
                "evidence_type": "document",
                "external_reference": f"doc://{code}",
                "title": "Evidence",
            },
        )
        completed = client.post(
            f"/api/v1/risk-controls/{control_id}/complete-implementation",
            headers=headers,
            json={"expected_version": 4, "summary": "done"},
        )
        return control_id, completed.json()["version"]

    cid, version = _ready("RC-EFF")
    effective = client.post(
        f"/api/v1/risk-controls/{cid}/verifications",
        headers=headers,
        json={
            "expected_version": version,
            "method": "test",
            "result": "effective",
            "evidence_refs": ["doc://RC-EFF"],
            "next_review_date": datetime.now(UTC).isoformat(),
        },
    )
    assert effective.json()["lifecycle_status"] == "verified_effective"

    cid, version = _ready("RC-PART")
    partial = client.post(
        f"/api/v1/risk-controls/{cid}/verifications",
        headers=headers,
        json={
            "expected_version": version,
            "method": "test",
            "result": "partially_effective",
            "evidence_refs": ["doc://RC-PART"],
            "next_review_date": datetime.now(UTC).isoformat(),
        },
    )
    assert partial.json()["lifecycle_status"] == "implemented"
    assert partial.json()["latest_effectiveness_result"] == "partially_effective"

    cid, version = _ready("RC-INEFF")
    ineffective = client.post(
        f"/api/v1/risk-controls/{cid}/verifications",
        headers=headers,
        json={
            "expected_version": version,
            "method": "test",
            "result": "ineffective",
            "evidence_refs": ["doc://RC-INEFF"],
            "findings": "failed",
        },
    )
    assert ineffective.json()["lifecycle_status"] == "verified_ineffective"


def test_invalid_transition_returns_422(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, hazard, *_ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _headers(org, token)
    created = client.post(
        "/api/v1/risk-controls",
        headers=headers,
        json=_create_payload(code="RC-INV", hazard_id=str(hazard.id.value)),
    )
    control_id = created.json()["id"]
    started = client.post(
        f"/api/v1/risk-controls/{control_id}/start-implementation",
        headers=headers,
        json={"expected_version": 1},
    )
    assert started.status_code == 422


def test_openapi_has_no_delete_for_risk_controls(
    enforced_auth_settings: AppSettings,
) -> None:
    client, *_ = _build_client(enforced_auth_settings, role=Role.admin())
    schema = client.get("/openapi.json").json()
    paths = schema.get("paths", {})
    assert "/api/v1/risk-controls/{control_id}" in paths
    assert "delete" not in paths["/api/v1/risk-controls/{control_id}"]
    assert (
        "/api/v1/risk-assessments/{assessment_id}/materialize-controls" in paths
        or any("materialize-controls" in path for path in paths)
    )
