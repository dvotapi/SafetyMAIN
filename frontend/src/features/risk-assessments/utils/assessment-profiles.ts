import type {
  AssessmentProfileDto,
  RiskFactorId,
} from "@/features/risk-assessments/types/risk-assessment-types";

/**
 * Minimal frontend profile catalog aligned with backend AssessmentProfileCode.
 * Not a full mirror of assessment_profiles.py — no bands, acceptable levels,
 * or review defaults. Documented limitation: no profile-list API.
 */
export interface AssessmentProfileCatalogEntry {
  code: AssessmentProfileDto;
  title: string;
  matrixSize: 3 | 5;
  requiredFactorIds: readonly RiskFactorId[];
}

function factors(...extra: RiskFactorId[]): readonly RiskFactorId[] {
  return ["probability", "severity", ...extra] as const;
}

export const ASSESSMENT_PROFILE_CATALOG: readonly AssessmentProfileCatalogEntry[] =
  [
    {
      code: "simple_3x3",
      title: "Simple 3×3 Matrix",
      matrixSize: 3,
      requiredFactorIds: factors(),
    },
    {
      code: "simple_5x5",
      title: "Simple 5×5 Matrix",
      matrixSize: 5,
      requiredFactorIds: factors(),
    },
    {
      code: "corporate_custom",
      title: "Corporate Custom",
      matrixSize: 5,
      requiredFactorIds: factors("business_impact"),
    },
    {
      code: "russian_occupational_risk",
      title: "Russian Occupational Risk",
      matrixSize: 5,
      requiredFactorIds: factors("exposure", "frequency"),
    },
    {
      code: "industrial_safety",
      title: "Industrial Safety",
      matrixSize: 5,
      requiredFactorIds: factors("detectability"),
    },
    {
      code: "fire_safety",
      title: "Fire Safety",
      matrixSize: 5,
      requiredFactorIds: factors("fire_consequence"),
    },
    {
      code: "environmental_risk",
      title: "Environmental Risk",
      matrixSize: 5,
      requiredFactorIds: factors("environmental_impact"),
    },
    {
      code: "transport_risk",
      title: "Transport Risk",
      matrixSize: 5,
      requiredFactorIds: factors(),
    },
    {
      code: "adr_risk",
      title: "ADR Risk",
      matrixSize: 5,
      requiredFactorIds: factors("exposure"),
    },
  ] as const;

const BY_CODE = new Map(
  ASSESSMENT_PROFILE_CATALOG.map((entry) => [entry.code, entry]),
);

export function getAssessmentProfileCatalogEntry(
  code: string,
): AssessmentProfileCatalogEntry | undefined {
  return BY_CODE.get(code as AssessmentProfileDto);
}

export function listAssessmentProfileCodes(): AssessmentProfileDto[] {
  return ASSESSMENT_PROFILE_CATALOG.map((entry) => entry.code);
}

export function extraFactorIds(
  entry: AssessmentProfileCatalogEntry,
): RiskFactorId[] {
  return entry.requiredFactorIds.filter(
    (id) => id !== "probability" && id !== "severity",
  );
}
