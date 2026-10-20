from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.organization import OrganizationNotFound
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from scripts.seed_document_types import (
    DOCUMENT_TYPE_CATALOG,
    DocumentTypeSeed,
    seed_document_types,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization

pytest_plugins = ("tests.infrastructure.db_fixtures",)


REQUIRED_CODES = frozenset(
    {
        "iot_profession",
        "iot_work_type",
        "production_instruction",
        "regulation_suot",
        "order",
        "briefing_program",
        "emergency_plan",
        "production_control_regulation",
        "dopog_cert",
        "driver_license",
        "ekv",
        "rtn_protocol",
        "attestation_protocol",
        "tractor_license",
        "drilling_license",
        "excavator_license",
        "medical_conclusion",
        "psychiatric_conclusion",
        "ot_briefing_repeat",
    }
)


# ---- catalog tests (no DB) ----


def test_catalog_codes_are_unique() -> None:
    codes = [seed.code for seed in DOCUMENT_TYPE_CATALOG]
    assert len(codes) == len(set(codes))


def test_catalog_contains_required_codes() -> None:
    present = {seed.code for seed in DOCUMENT_TYPE_CATALOG}
    missing = REQUIRED_CODES - present
    assert not missing, f"missing: {missing}"


def test_catalog_entries_are_valid_document_types() -> None:
    organization_id = OrganizationId(value=uuid4())
    now = datetime.now(UTC)
    for seed in DOCUMENT_TYPE_CATALOG:
        DocumentType.create(
            organization_id=organization_id,
            code=seed.code,
            title_ru=seed.title_ru,
            safety_domain=seed.safety_domain,
            subject_kind=seed.subject_kind,
            review_period_months=seed.review_period_months,
            validity_months=seed.validity_months,
            periodicity_months=seed.periodicity_months,
            warning_thresholds_days=seed.warning_thresholds_days,
            requires_acknowledgement=seed.requires_acknowledgement,
            requires_approval_order=seed.requires_approval_order,
            legal_basis=seed.legal_basis,
            legal_basis_reference=seed.legal_basis_reference,
            created_at=now,
        )


def test_repeat_briefing_has_periodicity() -> None:
    seeds = {s.code: s for s in DOCUMENT_TYPE_CATALOG}
    repeat = seeds["ot_briefing_repeat"]
    assert repeat.periodicity_months == 6
    assert repeat.subject_kind is DocumentSubjectKind.EMPLOYEE
    assert repeat.safety_domain is SafetyDomain.OCCUPATIONAL


# ---- DB tests ----


@pytest.fixture()
def _seeded_organization(sqlalchemy_session_factory):
    organization_id = OrganizationId(value=uuid4())
    with sqlalchemy_session_factory() as session:
        ensure_organization(session, organization_id)
        session.commit()
    return organization_id


@pytest.mark.db
def test_seed_is_idempotent(
    sqlalchemy_session_factory, _seeded_organization: OrganizationId
) -> None:
    now = datetime.now(UTC)
    first = seed_document_types(sqlalchemy_session_factory, _seeded_organization, now=now)
    assert len(first.created) == len(DOCUMENT_TYPE_CATALOG)
    assert first.skipped == ()

    second = seed_document_types(
        sqlalchemy_session_factory, _seeded_organization, now=now
    )
    assert second.created == ()
    assert len(second.skipped) == len(DOCUMENT_TYPE_CATALOG)


@pytest.mark.db
def test_seed_keeps_existing_codes_untouched(
    sqlalchemy_session_factory, _seeded_organization: OrganizationId
) -> None:
    # Pre-insert a different title under one of the seeded codes.
    from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
        SQLAlchemyUnitOfWork,
    )

    custom = DocumentType.create(
        organization_id=_seeded_organization,
        code="order",
        title_ru="Custom order title",
        safety_domain=SafetyDomain.FIRE,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        created_at=datetime.now(UTC),
    )
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        uow.document_types.add(custom)
        uow.commit()

    result = seed_document_types(
        sqlalchemy_session_factory, _seeded_organization, now=datetime.now(UTC)
    )
    assert "order" in result.skipped

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        reloaded = uow.document_types.get_by_code(_seeded_organization, "order")
        assert reloaded is not None
        assert reloaded.title_ru == "Custom order title"
        assert reloaded.safety_domain is SafetyDomain.FIRE


@pytest.mark.db
def test_seed_requires_existing_organization(sqlalchemy_session_factory) -> None:
    missing = OrganizationId(value=uuid4())
    with pytest.raises(OrganizationNotFound):
        seed_document_types(sqlalchemy_session_factory, missing, now=datetime.now(UTC))


@pytest.mark.db
def test_seed_is_organization_scoped(
    sqlalchemy_session_factory, _seeded_organization: OrganizationId
) -> None:
    seed_document_types(
        sqlalchemy_session_factory, _seeded_organization, now=datetime.now(UTC)
    )
    other = OrganizationId(value=uuid4())
    with sqlalchemy_session_factory() as session:
        ensure_organization(session, other)
        session.commit()
    other_result = seed_document_types(
        sqlalchemy_session_factory, other, now=datetime.now(UTC)
    )
    assert len(other_result.created) == len(DOCUMENT_TYPE_CATALOG)

    from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
        SQLAlchemyUnitOfWork,
    )

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        orig_types = uow.document_types.list(_seeded_organization, include_inactive=True)
    assert len(orig_types) == len(DOCUMENT_TYPE_CATALOG)
    assert all(dt.organization_id == _seeded_organization for dt in orig_types)


# make sure the dataclass is importable (defensive)
_ = DocumentTypeSeed
