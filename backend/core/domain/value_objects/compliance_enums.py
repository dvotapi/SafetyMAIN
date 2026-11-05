from __future__ import annotations

from enum import Enum


class SafetyDomain(str, Enum):
    """Safety domain a compliance document type belongs to (EPIC P11)."""

    OCCUPATIONAL = "occupational"
    INDUSTRIAL = "industrial"
    TRANSPORT_SECURITY = "transport_security"
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


class DocumentFileRole(str, Enum):
    """Role of an uploaded file (TASK-P11-012 D1, P11-001 amendment A2)."""

    WORKING = "working"
    SIGNED_SCAN = "signed_scan"
