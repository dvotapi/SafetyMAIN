from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    LegalBasisConfidence,
    SlotExclusionReason,
)

# Curated vocabulary «Вид» (TASK-P11-012 §2.1); metadata, not an enum.
SHELF_DOCUMENT_KINDS: tuple[str, ...] = (
    "Политика",
    "Положение",
    "Порядок / процедура",
    "Приказ",
    "Инструкция",
    "Программа",
    "План",
    "Журнал",
    "Перечень",
    "Протокол",
    "Акт",
    "Проект / паспорт",
    "Карта / реестр",
    "Удостоверение / свидетельство",
    "Договор / полис",
    "Отчёт",
    "Разрешение / лицензия",
)

EXCLUSION_COMMENT_MIN_LENGTH = 5
EXCLUSION_COMMENT_MAX_LENGTH = 1000
SOURCE_URL_MAX_LENGTH = 2048
_SOURCE_URL_SCHEMES = frozenset({"http", "https"})


def normalize_source_url(value: str | None) -> str | None:
    """Blank → None; otherwise an absolute http(s) URL (it is rendered as a link)."""
    if value is None:
        return None
    url = value.strip()
    if not url:
        return None
    if len(url) > SOURCE_URL_MAX_LENGTH:
        raise ValueError(f"Source URL must have at most {SOURCE_URL_MAX_LENGTH} characters.")
    parts = urlsplit(url)
    if parts.scheme.lower() not in _SOURCE_URL_SCHEMES or not parts.netloc:
        raise ValueError("Source URL must be an absolute http or https URL.")
    return url


class SlotLegalBasis(BaseModel):
    """Legal basis of a place («Основание»)."""

    model_config = ConfigDict(frozen=True)

    regulation: str = ""
    clause: str = ""
    quote: str = ""
    source_url: str | None = None
    confidence: LegalBasisConfidence = LegalBasisConfidence.NONE

    @field_validator("regulation", "clause", "quote")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("source_url")
    @classmethod
    def normalize_url(cls, value: str | None) -> str | None:
        return normalize_source_url(value)


class SlotExclusion(BaseModel):
    """Why and by whom a place was excluded; the place stays on the shelf (D11)."""

    model_config = ConfigDict(frozen=True)

    reason: SlotExclusionReason
    comment: str
    status_before: CuratedSlotStatus
    excluded_by: UserId
    excluded_at: datetime

    @field_validator("comment")
    @classmethod
    def require_comment(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < EXCLUSION_COMMENT_MIN_LENGTH:
            raise ValueError(
                f"Exclusion comment must have at least {EXCLUSION_COMMENT_MIN_LENGTH} characters."
            )
        if len(normalized) > EXCLUSION_COMMENT_MAX_LENGTH:
            raise ValueError(
                f"Exclusion comment must have at most {EXCLUSION_COMMENT_MAX_LENGTH} characters."
            )
        return normalized
