from __future__ import annotations

from datetime import datetime

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
        if value is None:
            return None
        return value.strip() or None


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
