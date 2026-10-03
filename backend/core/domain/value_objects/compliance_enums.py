from __future__ import annotations

from enum import Enum


class SafetyDomain(str, Enum):
    """Safety domain a compliance document type belongs to (EPIC P11)."""

    OCCUPATIONAL = "occupational"
    INDUSTRIAL = "industrial"
    LABOUR = "labour"
    FIRE = "fire"
    ENVIRONMENTAL = "environmental"
    ROAD = "road"
    DANGEROUS_GOODS = "dangerous_goods"


class DocumentSubjectKind(str, Enum):
    ORGANIZATION = "organization"
    EMPLOYEE = "employee"
    ASSET = "asset"


class ComplianceDocumentStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ComplianceDocumentSource(str, Enum):
    MANUAL = "manual"
    GENERATED = "generated"
    HR_FORM = "hr_form"
