"""Idempotent document-type catalog seeding (P11-001).

Seeds the organizational compliance document type catalog (D1) into one
organization. No administrative audit event is recorded because audit
requires an acting principal and the seed script runs without a session
owner (`bootstrap_admin` precedent). The script never creates an
organization: the operator seeds types for an existing one.

Re-running the script leaves the database unchanged: codes that already
exist in the organization are skipped.

The periods, acknowledgement/approval-order flags and warning thresholds in
`DOCUMENT_TYPE_CATALOG` are the D2 catalog confirmed by the product owner
on 2026-10-21. See
docs/tasks/TASK-P11-001-storage-and-compliance-documents.md.

Usage (inside the backend image, with DATABASE_URL set):

    python -m scripts.seed_document_types --organization-id <uuid>
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from backend.core.domain.entities.document_type import (
    DEFAULT_WARNING_THRESHOLDS_DAYS,
    DocumentType,
)
from backend.core.domain.exceptions.organization import OrganizationNotFound
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.infrastructure.persistence.sqlalchemy.engine import (
    create_engine,
    create_session_factory,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


@dataclass(frozen=True)
class DocumentTypeSeed:
    code: str
    title_ru: str
    safety_domain: SafetyDomain
    subject_kind: DocumentSubjectKind
    review_period_months: int | None = None
    validity_months: int | None = None
    periodicity_months: int | None = None
    warning_thresholds_days: tuple[int, ...] = DEFAULT_WARNING_THRESHOLDS_DAYS
    requires_acknowledgement: bool = False
    requires_approval_order: bool = False
    legal_basis: str = ""
    legal_basis_reference: str | None = None


@dataclass(frozen=True)
class SeedResult:
    created: tuple[str, ...]
    skipped: tuple[str, ...]


# Warning thresholds: Variant Б — longer thresholds for long-period documents
# (60+ months) and shorter ones for short-period documents (<= 12 months).
# A document whose period is <= 12 months lights up as "review-due" too far
# in advance under the default [90, 30, 14, 7]; a smaller set keeps the warning
# proportional to the lifecycle.
_LONG_THRESHOLDS: tuple[int, ...] = (90, 30, 14, 7)
_SHORT_THRESHOLDS: tuple[int, ...] = (30, 14, 7, 3)

# D2 — confirmed by the product owner on 2026-10-21.
DOCUMENT_TYPE_CATALOG: tuple[DocumentTypeSeed, ...] = (
    # ---- Organization documents ----
    DocumentTypeSeed(
        code="iot_profession",
        title_ru="Инструкция по охране труда для профессии",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
        legal_basis="Приказ Минтруда России от 29.10.2021 № 772н",
    ),
    DocumentTypeSeed(
        code="iot_work_type",
        title_ru="Инструкция по охране труда для вида работ",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
        legal_basis="Приказ Минтруда России от 29.10.2021 № 772н",
    ),
    DocumentTypeSeed(
        code="production_instruction",
        title_ru="Производственная инструкция",
        safety_domain=SafetyDomain.INDUSTRIAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
    ),
    DocumentTypeSeed(
        code="regulation_suot",
        title_ru="Положение о системе управления охраной труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
        legal_basis="Приказ Минтруда России от 29.10.2021 № 776н",
    ),
    DocumentTypeSeed(
        code="order",
        title_ru="Приказ",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
    ),
    DocumentTypeSeed(
        code="briefing_program",
        title_ru="Программа инструктажа по охране труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
        legal_basis="Постановление Правительства РФ от 24.12.2021 № 2464",
    ),
    DocumentTypeSeed(
        code="emergency_plan",
        title_ru="План мероприятий по локализации и ликвидации аварий",
        safety_domain=SafetyDomain.INDUSTRIAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
        legal_basis="Постановление Правительства РФ от 15.09.2020 № 1437",
    ),
    DocumentTypeSeed(
        code="production_control_regulation",
        title_ru="Положение о производственном контроле",
        safety_domain=SafetyDomain.INDUSTRIAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        requires_acknowledgement=True,
        requires_approval_order=True,
        legal_basis="Постановление Правительства РФ от 18.12.2020 № 2168",
    ),
    # ---- Employee documents (validity) ----
    DocumentTypeSeed(
        code="dopog_cert",
        title_ru="Свидетельство ДОПОГ водителя",
        safety_domain=SafetyDomain.DANGEROUS_GOODS,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="ДОПОГ 8.2.2.8",
    ),
    DocumentTypeSeed(
        code="driver_license",
        title_ru="Водительское удостоверение",
        safety_domain=SafetyDomain.ROAD,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=120,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Федеральный закон от 10.12.1995 № 196-ФЗ, ст. 25",
    ),
    DocumentTypeSeed(
        code="ekv",
        title_ru="Единая книжка взрывника",
        safety_domain=SafetyDomain.INDUSTRIAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
    ),
    DocumentTypeSeed(
        code="rtn_protocol",
        title_ru="Протокол аттестации по промышленной безопасности (Ростехнадзор)",
        safety_domain=SafetyDomain.INDUSTRIAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Постановление Правительства РФ от 25.10.2019 № 1365",
    ),
    DocumentTypeSeed(
        code="attestation_protocol",
        title_ru="Протокол проверки знаний требований промышленной безопасности",
        safety_domain=SafetyDomain.INDUSTRIAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Постановление Правительства РФ от 25.10.2019 № 1365",
    ),
    DocumentTypeSeed(
        code="tractor_license",
        title_ru="Удостоверение тракториста-машиниста",
        safety_domain=SafetyDomain.ROAD,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=120,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Постановление Правительства РФ от 12.07.1999 № 796",
    ),
    DocumentTypeSeed(
        code="drilling_license",
        title_ru="Удостоверение тракториста-машиниста с отметкой «буровая установка»",
        safety_domain=SafetyDomain.ROAD,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=120,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Постановление Правительства РФ от 12.07.1999 № 796",
    ),
    DocumentTypeSeed(
        code="excavator_license",
        title_ru="Удостоверение тракториста-машиниста с отметкой «экскаватор»",
        safety_domain=SafetyDomain.ROAD,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=120,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Постановление Правительства РФ от 12.07.1999 № 796",
    ),
    DocumentTypeSeed(
        code="medical_conclusion",
        title_ru="Медицинское заключение по результатам периодического осмотра",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=12,
        warning_thresholds_days=_SHORT_THRESHOLDS,
        legal_basis="Приказ Минздрава России от 28.01.2021 № 29н",
    ),
    DocumentTypeSeed(
        code="psychiatric_conclusion",
        title_ru="Психиатрическое заключение",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=60,
        warning_thresholds_days=_LONG_THRESHOLDS,
        legal_basis="Приказ Минздрава России от 20.05.2022 № 342н",
    ),
    # ---- Repeating briefings (periodicity) ----
    DocumentTypeSeed(
        code="ot_briefing_introductory",
        title_ru="Вводный инструктаж по охране труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        legal_basis="Постановление Правительства РФ от 24.12.2021 № 2464",
    ),
    DocumentTypeSeed(
        code="ot_briefing_primary",
        title_ru="Первичный инструктаж по охране труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        legal_basis="Постановление Правительства РФ от 24.12.2021 № 2464",
    ),
    DocumentTypeSeed(
        code="ot_briefing_repeat",
        title_ru="Повторный инструктаж по охране труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        periodicity_months=6,
        warning_thresholds_days=_SHORT_THRESHOLDS,
        legal_basis="Постановление Правительства РФ от 24.12.2021 № 2464",
    ),
    DocumentTypeSeed(
        code="ot_briefing_unscheduled",
        title_ru="Внеплановый инструктаж по охране труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        legal_basis="Постановление Правительства РФ от 24.12.2021 № 2464",
    ),
    DocumentTypeSeed(
        code="ot_briefing_targeted",
        title_ru="Целевой инструктаж по охране труда",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        legal_basis="Постановление Правительства РФ от 24.12.2021 № 2464",
    ),
)


def seed_document_types(
    session_factory: sessionmaker,
    organization_id: OrganizationId,
    *,
    now: datetime,
) -> SeedResult:
    """Add missing types to the organization. Returns created and skipped codes."""
    created: list[str] = []
    skipped: list[str] = []
    with SQLAlchemyUnitOfWork(session_factory) as uow:
        uow.organizations.get(organization_id)  # raises OrganizationNotFound
        for seed in DOCUMENT_TYPE_CATALOG:
            existing = uow.document_types.get_by_code(organization_id, seed.code)
            if existing is not None:
                skipped.append(seed.code)
                continue
            uow.document_types.add(
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
            )
            created.append(seed.code)
        uow.commit()
    return SeedResult(created=tuple(created), skipped=tuple(skipped))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization-id", required=True, type=UUID)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL must be set.")

    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)
    try:
        result = seed_document_types(
            session_factory,
            OrganizationId(value=args.organization_id),
            now=datetime.now(UTC),
        )
    except OrganizationNotFound as error:
        raise SystemExit(f"Organization not found: {error}") from error

    print(f"created={len(result.created)}: {', '.join(result.created) or '-'}")
    print(f"skipped={len(result.skipped)}: {', '.join(result.skipped) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


_ = field  # keep dataclass helper import stable
