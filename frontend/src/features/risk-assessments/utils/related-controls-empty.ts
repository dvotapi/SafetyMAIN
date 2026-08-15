import type {
  ControlMeasure,
  RelatedRiskControlSummary,
} from "@/features/risk-assessments/types/risk-assessment-types";

export type RelatedControlsEmptyKind =
  "no_proposed" | "not_materialized" | null;

/**
 * Distinguishes empty related-controls outcomes for Object Page messaging.
 */
export function relatedControlsEmptyKind(
  proposedControls: readonly ControlMeasure[],
  materialized: readonly RelatedRiskControlSummary[],
): RelatedControlsEmptyKind {
  if (materialized.length > 0) {
    return null;
  }
  if (proposedControls.length === 0) {
    return "no_proposed";
  }
  return "not_materialized";
}
