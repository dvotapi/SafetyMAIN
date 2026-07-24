from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.domain.exceptions.risk_control import (
    DuplicateRiskControlCode,
    RiskControlVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_control_components import (
    ControlEffectivenessVerification,
    EvidenceReference,
)
from backend.core.domain.value_objects.safety_enums import (
    EffectivenessResult,
    EvidenceType,
    RiskControlStatus,
    VerificationType,
)
from backend.core.domain.value_objects.safety_ids import RiskAssessmentId
from backend.core.infrastructure.persistence.sqlalchemy.repositories.risk_control_repository import (
    SQLAlchemyRiskControlRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_sqlalchemy_risk_control_contracts import (
    _SeedingRiskControlRepository,
)
from tests.fixtures.risk_controls import (
    risk_control_draft,
    risk_control_rich_round_trip,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
def test_risk_control_survives_engine_restart(database_url: str, migrated_engine) -> None:
    organization_id = OrganizationId(value=uuid4())
    actor_id = UserId(value=uuid4())
    now = datetime.now(UTC)

    factory_a = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    with factory_a() as session:
        ensure_organization(session, organization_id)
        ensure_user(session, actor_id)
        control = risk_control_rich_round_trip(
            organization_id=organization_id,
            actor=actor_id,
        )
        _SeedingRiskControlRepository(session).add(control)
        session.commit()
        control_id = control.id
        expected_dump = control.model_dump(mode="json")

    migrated_engine.dispose()
    engine_b = create_engine(database_url)
    try:
        factory_b = sessionmaker(bind=engine_b, expire_on_commit=False)
        with factory_b() as session:
            loaded = SQLAlchemyRiskControlRepository(session).get(
                organization_id,
                control_id,
            )
            assert loaded is not None
            assert loaded.model_dump(mode="json") == expected_dump
            assert loaded.lifecycle_status is RiskControlStatus.VERIFIED_EFFECTIVE

            mutated = loaded.add_evidence(
                evidence=EvidenceReference(
                    evidence_type=EvidenceType.INSPECTION_RECORD,
                    external_reference="doc://post-restart",
                    title="Post restart evidence",
                    captured_at=now,
                    captured_by=actor_id,
                ),
                at=now,
                actor_id=actor_id,
                expected_version=loaded.version,
                allow_after_implemented=True,
            )
            SQLAlchemyRiskControlRepository(session).save(
                mutated,
                expected_version=loaded.version,
            )
            session.commit()
            mutated_version = mutated.version

        with factory_b() as session:
            again = SQLAlchemyRiskControlRepository(session).get(
                organization_id,
                control_id,
            )
            assert again is not None
            assert again.version == mutated_version
            assert any(
                item.external_reference == "doc://post-restart"
                for item in again.evidence
            )
    finally:
        engine_b.dispose()


@pytest.mark.db
def test_materialization_uniqueness_survives_restart(
    database_url: str,
    migrated_engine,
) -> None:
    organization_id = OrganizationId(value=uuid4())
    actor_id = UserId(value=uuid4())
    assessment_id = RiskAssessmentId(value=uuid4())
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)

    with factory() as session:
        ensure_organization(session, organization_id)
        ensure_user(session, actor_id)
        control = risk_control_draft(
            organization_id=organization_id,
            actor=actor_id,
            risk_assessment_id=assessment_id,
            source_control_reference="embedded-1",
            code="RC-MAT-1",
        )
        _SeedingRiskControlRepository(session).add(control)
        session.commit()

    migrated_engine.dispose()
    engine_b = create_engine(database_url)
    try:
        factory2 = sessionmaker(bind=engine_b, expire_on_commit=False)
        with factory2() as session:
            repo = _SeedingRiskControlRepository(session)
            assert repo.exists_for_source(
                organization_id,
                assessment_id,
                "embedded-1",
            )
            duplicate = risk_control_draft(
                organization_id=organization_id,
                actor=actor_id,
                risk_assessment_id=assessment_id,
                source_control_reference="embedded-1",
                code="RC-MAT-2",
            )
            with pytest.raises(DuplicateRiskControlCode):
                repo.add(duplicate)
            session.rollback()
    finally:
        engine_b.dispose()


@pytest.mark.db
def test_stale_verification_does_not_partially_persist(migrated_engine) -> None:
    organization_id = OrganizationId(value=uuid4())
    actor_id = UserId(value=uuid4())
    now = datetime.now(UTC)
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)

    with factory() as session:
        ensure_organization(session, organization_id)
        ensure_user(session, actor_id)
        control = risk_control_rich_round_trip(
            organization_id=organization_id,
            actor=actor_id,
        )
        repo = _SeedingRiskControlRepository(session)
        repo.add(control)
        session.commit()
        control_id = control.id
        version = control.version

    with factory() as session:
        repo = SQLAlchemyRiskControlRepository(session)
        a = repo.get(organization_id, control_id)
        b = repo.get(organization_id, control_id)
        assert a is not None and b is not None
        a2, _ = a.record_verification(
            verification=ControlEffectivenessVerification(
                verification_type=VerificationType.SCHEDULED_REVIEW,
                method="Follow-up",
                performed_at=now,
                performed_by=actor_id,
                result=EffectivenessResult.PARTIALLY_EFFECTIVE,
                evidence_refs=("doc://photo-1",),
                findings="Gap found",
                next_review_date=now + timedelta(days=30),
            ),
            at=now,
            actor_id=actor_id,
            expected_version=version,
        )
        repo.save(a2, expected_version=version)
        session.commit()

        with pytest.raises(RiskControlVersionConflict):
            b2, _ = b.record_verification(
                verification=ControlEffectivenessVerification(
                    verification_type=VerificationType.OTHER,
                    method="Stale",
                    performed_at=now,
                    performed_by=actor_id,
                    result=EffectivenessResult.INEFFECTIVE,
                    evidence_refs=("doc://photo-1",),
                    findings="Should not persist",
                ),
                at=now,
                actor_id=actor_id,
                expected_version=version,
            )
            repo.save(b2, expected_version=version)
        session.rollback()

    with factory() as session:
        loaded = SQLAlchemyRiskControlRepository(session).get(
            organization_id,
            control_id,
        )
        assert loaded is not None
        assert len(loaded.verifications) == 2
        assert (
            loaded.verifications[-1].result is EffectivenessResult.PARTIALLY_EFFECTIVE
        )
        assert all(item.method != "Stale" for item in loaded.verifications)
