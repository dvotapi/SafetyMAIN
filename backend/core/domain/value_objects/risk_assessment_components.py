from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    CompetencyReferenceCode,
    ControlType,
    Probability,
    ReviewTrigger,
    RiskAcceptanceDecision,
    RiskFactorCode,
    RiskLevel,
    Severity,
)
from backend.core.domain.value_objects.safety_ids import ControlId


class AssessedObjectRef(BaseModel):
    """Typed operational context reference without owning the target aggregate."""

    model_config = ConfigDict(frozen=True)

    object_type: AssessedObjectType
    reference: str

    @field_validator("reference")
    @classmethod
    def normalize_reference(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Assessed object reference must not be empty.")
        if len(normalized) > 256:
            raise ValueError("Assessed object reference must be at most 256 characters.")
        return normalized


class RiskFactorScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    factor: RiskFactorCode
    score: int = Field(ge=1, le=5)


class RiskEvaluation(BaseModel):
    """Inherent or residual risk evaluation payload."""

    model_config = ConfigDict(frozen=True)

    factors: tuple[RiskFactorScore, ...]
    level: RiskLevel
    explanation: str = ""

    @field_validator("explanation")
    @classmethod
    def normalize_explanation(cls, value: str) -> str:
        return value.strip()

    @property
    def probability(self) -> Probability | None:
        for factor in self.factors:
            if factor.factor is RiskFactorCode.PROBABILITY:
                return _score_to_probability(factor.score)
        return None

    @property
    def severity(self) -> Severity | None:
        for factor in self.factors:
            if factor.factor is RiskFactorCode.SEVERITY:
                return _score_to_severity(factor.score)
        return None

    def factor_map(self) -> dict[str, int]:
        return {factor.factor.value: factor.score for factor in self.factors}


class ControlMeasure(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: ControlId = Field(frozen=True)
    control_type: ControlType
    description: str
    responsible: str | None = None
    implemented: bool = False
    effective: bool | None = None

    @field_validator("description")
    @classmethod
    def require_description(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Control description is required.")
        return normalized

    @field_validator("responsible")
    @classmethod
    def normalize_responsible(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RiskAcceptance(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: RiskAcceptanceDecision
    reviewer_id: UserId | None = None
    justification: str = ""
    approved_at: datetime | None = None

    @field_validator("justification")
    @classmethod
    def normalize_justification(cls, value: str) -> str:
        return value.strip()


class ReviewSchedule(BaseModel):
    model_config = ConfigDict(frozen=True)

    review_due_date: datetime | None = None
    review_frequency_days: int | None = Field(default=None, ge=1)
    review_reason: str | None = None
    triggered_by: ReviewTrigger | None = None

    @field_validator("review_reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


def _score_to_probability(score: int) -> Probability:
    mapping = {
        1: Probability.RARE,
        2: Probability.UNLIKELY,
        3: Probability.POSSIBLE,
        4: Probability.LIKELY,
        5: Probability.ALMOST_CERTAIN,
    }
    return mapping.get(score, Probability.POSSIBLE)


def _score_to_severity(score: int) -> Severity:
    mapping = {
        1: Severity.INSIGNIFICANT,
        2: Severity.MINOR,
        3: Severity.MODERATE,
        4: Severity.MAJOR,
        5: Severity.CATASTROPHIC,
    }
    return mapping.get(score, Severity.MODERATE)


def evaluation_to_dict(evaluation: RiskEvaluation | None) -> dict[str, Any] | None:
    if evaluation is None:
        return None
    return {
        "factors": [
            {"factor": item.factor.value, "score": item.score}
            for item in evaluation.factors
        ],
        "level": evaluation.level.value,
        "explanation": evaluation.explanation,
    }


def evaluation_from_dict(payload: dict[str, Any] | None) -> RiskEvaluation | None:
    if payload is None:
        return None
    return RiskEvaluation(
        factors=tuple(
            RiskFactorScore(factor=RiskFactorCode(item["factor"]), score=item["score"])
            for item in payload.get("factors", ())
        ),
        level=RiskLevel(payload["level"]),
        explanation=payload.get("explanation", ""),
    )


def control_to_dict(control: ControlMeasure) -> dict[str, Any]:
    return {
        "id": str(control.id.value),
        "control_type": control.control_type.value,
        "description": control.description,
        "responsible": control.responsible,
        "implemented": control.implemented,
        "effective": control.effective,
    }


def control_from_dict(payload: dict[str, Any]) -> ControlMeasure:
    return ControlMeasure(
        id=ControlId(value=UUID(payload["id"])),
        control_type=ControlType(payload["control_type"]),
        description=payload["description"],
        responsible=payload.get("responsible"),
        implemented=bool(payload.get("implemented", False)),
        effective=payload.get("effective"),
    )


def competency_values(
    values: tuple[CompetencyReferenceCode, ...] | list[CompetencyReferenceCode],
) -> tuple[CompetencyReferenceCode, ...]:
    seen: set[CompetencyReferenceCode] = set()
    ordered: list[CompetencyReferenceCode] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)
