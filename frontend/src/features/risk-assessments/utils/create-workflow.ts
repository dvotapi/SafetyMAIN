import type { RiskAssessmentFormValues } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import {
  emptyRiskEvaluationFormValues,
  isRiskEvaluationFormEmpty,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";

/** True when create should follow POST with a risk-input PATCH. */
export function shouldPatchRiskInputsAfterCreate(
  values: RiskAssessmentFormValues,
): boolean {
  if (!isRiskEvaluationFormEmpty(values.inherentRisk)) {
    return true;
  }
  if (!isRiskEvaluationFormEmpty(values.residualRisk)) {
    return true;
  }
  if (values.controls.length > 0) {
    return true;
  }
  if (values.acceptanceDecision !== null) {
    return true;
  }
  return false;
}

export function emptyExtraFactorScoresForProfile(
  factorIds: readonly string[],
): Record<string, number | null> {
  const scores: Record<string, number | null> = {};
  for (const factorId of factorIds) {
    if (factorId === "probability" || factorId === "severity") {
      continue;
    }
    scores[factorId] = null;
  }
  return scores;
}

export function resetEvaluationForProfile(
  factorIds: readonly string[],
): typeof emptyRiskEvaluationFormValues & {
  extraFactorScores: Record<string, number | null>;
} {
  return {
    ...emptyRiskEvaluationFormValues,
    extraFactorScores: emptyExtraFactorScoresForProfile(factorIds),
  };
}
