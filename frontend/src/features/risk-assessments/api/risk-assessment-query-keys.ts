import type { RiskAssessmentListParams } from "@/features/risk-assessments/types/risk-assessment-types";

export const riskAssessmentKeys = {
  all: (organizationId: string | null) =>
    ["risk-assessments", organizationId ?? "none"] as const,
  lists: (organizationId: string | null) =>
    [...riskAssessmentKeys.all(organizationId), "list"] as const,
  list: (organizationId: string | null, filters: RiskAssessmentListParams) =>
    [...riskAssessmentKeys.lists(organizationId), filters] as const,
  details: (organizationId: string | null) =>
    [...riskAssessmentKeys.all(organizationId), "detail"] as const,
  detail: (organizationId: string | null, riskAssessmentId: string) =>
    [...riskAssessmentKeys.details(organizationId), riskAssessmentId] as const,
  relatedControls: (organizationId: string | null, riskAssessmentId: string) =>
    [
      ...riskAssessmentKeys.detail(organizationId, riskAssessmentId),
      "related-controls",
    ] as const,
  activity: (organizationId: string | null, riskAssessmentId: string) =>
    [
      ...riskAssessmentKeys.detail(organizationId, riskAssessmentId),
      "activity",
    ] as const,
};
