"""Signed scans and inline view URLs (TASK-P11-012 D1, P11-001 amendments A2–A4)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.value_objects import OrganizationId, Role
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.test_compliance_document_files_api import (
    SHA256_HEX,
    _build_client,
    _headers,
)
from tests.fixtures.compliance_documents import (
    advance_to_active,
    advance_to_approved,
    compliance_document_draft,
)

BASE = "/api/v1/compliance-documents"


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


def _seed(ctx: dict[str, Any], stage: str) -> ComplianceDocument:
    draft = compliance_document_draft(ctx["document_type"], code=f"ПОТБ-{uuid4().hex[:4]}")
    if stage == "approved":
        document = advance_to_approved(draft)
    elif stage == "active":
        document = advance_to_active(draft, ctx["document_type"])
    else:
        document = draft
    ctx["compliance_documents"].add(document)
    return document


def _upload_scan(
    ctx: dict[str, Any], document: ComplianceDocument, *, content_type: str = "application/pdf"
) -> Any:
    headers = _headers(ctx["organization_id"], ctx["token"])
    issued = ctx["client"].post(
        f"{BASE}/{document.id.value}/signed-scan/upload-url",
        headers=headers,
        json={
            "filename": "Подписанный приказ.pdf",
            "content_type": content_type,
            "size_bytes": 4096,
            "sha256": SHA256_HEX,
        },
    )
    if issued.status_code != 200:
        return issued
    key = issued.json()["key"]
    ctx["storage"].store_object(
        key, size_bytes=4096, content_type=content_type, sha256=SHA256_HEX
    )
    return ctx["client"].post(
        f"{BASE}/{document.id.value}/signed-scan/confirm",
        headers=headers,
        json={
            "expected_version": document.version,
            "key": key,
            "size_bytes": 4096,
            "sha256": SHA256_HEX,
            "content_type": content_type,
            "original_filename": "Подписанный приказ.pdf",
        },
    )


@pytest.mark.parametrize("stage", ["approved", "active"])
def test_signed_scan_attaches_to_non_draft_documents(
    enforced_auth_settings: AppSettings, stage: str
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    document = _seed(ctx, stage)
    working = document.current_file
    assert working is not None

    confirmed = _upload_scan(ctx, document)

    assert confirmed.status_code == 200, confirmed.json()
    body = confirmed.json()
    assert body["status"] == stage
    assert body["current_signed_scan"]["role"] == "signed_scan"
    assert body["current_signed_scan"]["original_filename"] == "Подписанный приказ.pdf"
    assert body["current_file"]["id"] == str(working.id.value)
    assert body["current_file"]["role"] == "working"
    actions = [e.action.value for e in ctx["audit_events"].snapshot().values()]
    assert actions.count("compliance.document.signed_scan_attached") == 1


def test_signed_scan_is_refused_for_a_draft(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    document = _seed(ctx, "draft")

    assert_error_envelope(
        _upload_scan(ctx, document),
        status_code=422,
        code="compliance_document_cannot_be_modified",
    )


def test_signed_scan_accepts_only_pdf_jpeg_png(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    document = _seed(ctx, "active")

    response = _upload_scan(
        ctx,
        document,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert_error_envelope(
        response, status_code=422, code="compliance_document_file_type_not_allowed"
    )
    assert _upload_scan(ctx, document, content_type="image/png").status_code == 200


def test_working_file_upload_on_an_active_document_is_still_refused(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    document = _seed(ctx, "active")

    response = ctx["client"].post(
        f"{BASE}/{document.id.value}/files/upload-url",
        headers=_headers(ctx["organization_id"], ctx["token"]),
        json={
            "filename": "x.pdf",
            "content_type": "application/pdf",
            "size_bytes": 10,
            "sha256": SHA256_HEX,
        },
    )

    assert response.status_code == 422


def test_download_and_view_urls(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    document = _seed(ctx, "active")
    headers = _headers(ctx["organization_id"], ctx["token"])

    assert_error_envelope(
        ctx["client"].get(
            f"{BASE}/{document.id.value}/files/signed-scan/current/download-url",
            headers=headers,
        ),
        status_code=404,
        code="compliance_document_file_not_found",
    )
    scan = _upload_scan(ctx, document).json()["current_signed_scan"]

    download = ctx["client"].get(
        f"{BASE}/{document.id.value}/files/signed-scan/current/download-url", headers=headers
    )
    view = ctx["client"].get(
        f"{BASE}/{document.id.value}/files/{scan['id']}/view-url", headers=headers
    )

    assert download.status_code == 200
    assert "attachment" in download.json()["url"]
    assert view.status_code == 200
    assert "inline" in view.json()["url"]
    assert "attachment" not in view.json()["url"]
    assert_error_envelope(
        ctx["client"].get(f"{BASE}/{document.id.value}/files/{uuid4()}/view-url", headers=headers),
        status_code=404,
        code="compliance_document_file_not_found",
    )
    versions = ctx["client"].get(f"{BASE}/{document.id.value}/files/versions", headers=headers)
    assert [item["role"] for item in versions.json()["items"]] == ["working", "signed_scan"]


def test_view_url_of_another_organization_is_404(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    foreign = compliance_document_draft(organization_id=OrganizationId(value=uuid4()))
    ctx["compliance_documents"].add(foreign)
    headers = _headers(ctx["organization_id"], ctx["token"])

    response = ctx["client"].get(
        f"{BASE}/{foreign.id.value}/files/{uuid4()}/view-url", headers=headers
    )

    assert_error_envelope(response, status_code=404, code="compliance_document_not_found")


def test_auditor_reads_but_cannot_attach_a_signed_scan(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.auditor())
    document = _seed(ctx, "active")
    headers = _headers(ctx["organization_id"], ctx["token"])

    assert _upload_scan(ctx, document).status_code == 403
    versions = ctx["client"].get(f"{BASE}/{document.id.value}/files/versions", headers=headers)
    unknown = ctx["client"].get(
        f"{BASE}/{document.id.value}/files/{uuid4()}/view-url", headers=headers
    )
    assert versions.status_code == 200
    assert unknown.status_code == 404
