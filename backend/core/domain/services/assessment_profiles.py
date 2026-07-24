from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects.safety_enums import (
    AssessmentProfileCode,
    RiskFactorCode,
    RiskLevel,
)


@dataclass(frozen=True, slots=True)
class AssessmentProfile:
    """Built-in methodology profile (not embedded formulas in the aggregate)."""

    code: AssessmentProfileCode
    title: str
    factors: tuple[RiskFactorCode, ...]
    matrix_size: int
    acceptable_levels: frozenset[RiskLevel]
    default_review_frequency_days: int
    description: str


_MATRIX_3X3: dict[tuple[int, int], RiskLevel] = {
    (1, 1): RiskLevel.LOW,
    (1, 2): RiskLevel.LOW,
    (1, 3): RiskLevel.MEDIUM,
    (2, 1): RiskLevel.LOW,
    (2, 2): RiskLevel.MEDIUM,
    (2, 3): RiskLevel.HIGH,
    (3, 1): RiskLevel.MEDIUM,
    (3, 2): RiskLevel.HIGH,
    (3, 3): RiskLevel.EXTREME,
}

_MATRIX_5X5: dict[tuple[int, int], RiskLevel] = {
    (p, s): (
        RiskLevel.LOW
        if p * s <= 4
        else RiskLevel.MEDIUM
        if p * s <= 9
        else RiskLevel.HIGH
        if p * s <= 15
        else RiskLevel.EXTREME
    )
    for p in range(1, 6)
    for s in range(1, 6)
}


def _profile(
    code: AssessmentProfileCode,
    *,
    title: str,
    matrix_size: int,
    default_review_frequency_days: int,
    description: str,
    acceptable: frozenset[RiskLevel] | None = None,
    extra_factors: tuple[RiskFactorCode, ...] = (),
) -> AssessmentProfile:
    factors = (
        RiskFactorCode.PROBABILITY,
        RiskFactorCode.SEVERITY,
        *extra_factors,
    )
    return AssessmentProfile(
        code=code,
        title=title,
        factors=factors,
        matrix_size=matrix_size,
        acceptable_levels=acceptable
        or frozenset({RiskLevel.LOW, RiskLevel.MEDIUM}),
        default_review_frequency_days=default_review_frequency_days,
        description=description,
    )


BUILT_IN_ASSESSMENT_PROFILES: dict[AssessmentProfileCode, AssessmentProfile] = {
    AssessmentProfileCode.SIMPLE_3X3: _profile(
        AssessmentProfileCode.SIMPLE_3X3,
        title="Simple 3×3 Matrix",
        matrix_size=3,
        default_review_frequency_days=365,
        description="Generic probability × severity 3×3 matrix.",
    ),
    AssessmentProfileCode.SIMPLE_5X5: _profile(
        AssessmentProfileCode.SIMPLE_5X5,
        title="Simple 5×5 Matrix",
        matrix_size=5,
        default_review_frequency_days=365,
        description="Generic probability × severity 5×5 matrix.",
    ),
    AssessmentProfileCode.CORPORATE_CUSTOM: _profile(
        AssessmentProfileCode.CORPORATE_CUSTOM,
        title="Corporate Custom",
        matrix_size=5,
        default_review_frequency_days=180,
        description="Organization-defined methodology placeholder.",
        extra_factors=(RiskFactorCode.BUSINESS_IMPACT,),
    ),
    AssessmentProfileCode.RUSSIAN_OCCUPATIONAL_RISK: _profile(
        AssessmentProfileCode.RUSSIAN_OCCUPATIONAL_RISK,
        title="Russian Occupational Risk",
        matrix_size=5,
        default_review_frequency_days=365,
        description="Configurable occupational risk profile for Russian OHS practice.",
        extra_factors=(RiskFactorCode.EXPOSURE, RiskFactorCode.FREQUENCY),
    ),
    AssessmentProfileCode.INDUSTRIAL_SAFETY: _profile(
        AssessmentProfileCode.INDUSTRIAL_SAFETY,
        title="Industrial Safety",
        matrix_size=5,
        default_review_frequency_days=180,
        description="Industrial safety assessment profile.",
        extra_factors=(RiskFactorCode.DETECTABILITY,),
        acceptable=frozenset({RiskLevel.LOW}),
    ),
    AssessmentProfileCode.FIRE_SAFETY: _profile(
        AssessmentProfileCode.FIRE_SAFETY,
        title="Fire Safety",
        matrix_size=5,
        default_review_frequency_days=365,
        description="Fire safety risk profile.",
        extra_factors=(RiskFactorCode.FIRE_CONSEQUENCE,),
    ),
    AssessmentProfileCode.ENVIRONMENTAL_RISK: _profile(
        AssessmentProfileCode.ENVIRONMENTAL_RISK,
        title="Environmental Risk",
        matrix_size=5,
        default_review_frequency_days=365,
        description="Environmental risk profile.",
        extra_factors=(RiskFactorCode.ENVIRONMENTAL_IMPACT,),
    ),
    AssessmentProfileCode.TRANSPORT_RISK: _profile(
        AssessmentProfileCode.TRANSPORT_RISK,
        title="Transport Risk",
        matrix_size=5,
        default_review_frequency_days=180,
        description="Transport operations risk profile.",
    ),
    AssessmentProfileCode.ADR_RISK: _profile(
        AssessmentProfileCode.ADR_RISK,
        title="ADR Risk",
        matrix_size=5,
        default_review_frequency_days=180,
        description="Dangerous goods transport risk profile.",
        extra_factors=(RiskFactorCode.EXPOSURE,),
        acceptable=frozenset({RiskLevel.LOW}),
    ),
}


def get_assessment_profile(code: AssessmentProfileCode) -> AssessmentProfile:
    try:
        return BUILT_IN_ASSESSMENT_PROFILES[code]
    except KeyError as exc:
        raise ValueError(f"Unknown assessment profile: {code}") from exc


def resolve_matrix_level(
    *,
    matrix_size: int,
    probability_score: int,
    severity_score: int,
) -> RiskLevel:
    if matrix_size == 3:
        matrix = _MATRIX_3X3
        max_score = 3
    else:
        matrix = _MATRIX_5X5
        max_score = 5
    if not (1 <= probability_score <= max_score and 1 <= severity_score <= max_score):
        raise ValueError(
            f"Scores must be between 1 and {max_score} for matrix size {matrix_size}."
        )
    return matrix[(probability_score, severity_score)]


def probability_to_score(value: str | int, *, matrix_size: int) -> int:
    if isinstance(value, int):
        return value
    from backend.core.domain.value_objects.safety_enums import Probability

    ranking = {
        Probability.RARE: 1,
        Probability.UNLIKELY: 2,
        Probability.POSSIBLE: 3,
        Probability.LIKELY: 4,
        Probability.ALMOST_CERTAIN: 5,
    }
    score = ranking[Probability(value)]
    if matrix_size == 3:
        return min(3, max(1, round(score * 3 / 5)))
    return score


def severity_to_score(value: str | int, *, matrix_size: int) -> int:
    if isinstance(value, int):
        return value
    from backend.core.domain.value_objects.safety_enums import Severity

    ranking = {
        Severity.INSIGNIFICANT: 1,
        Severity.MINOR: 2,
        Severity.MODERATE: 3,
        Severity.MAJOR: 4,
        Severity.CATASTROPHIC: 5,
    }
    score = ranking[Severity(value)]
    if matrix_size == 3:
        return min(3, max(1, round(score * 3 / 5)))
    return score
