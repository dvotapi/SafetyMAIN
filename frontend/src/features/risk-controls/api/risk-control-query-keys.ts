import type { RiskControlListParams } from "@/features/risk-controls/types/risk-control-dto";

export const riskControlKeys = {
  all: (organizationId: string | null) =>
    ["risk-controls", organizationId ?? "none"] as const,
  lists: (organizationId: string | null) =>
    [...riskControlKeys.all(organizationId), "list"] as const,
  list: (organizationId: string | null, filters: RiskControlListParams) =>
    [...riskControlKeys.lists(organizationId), filters] as const,
  forAssessment: (organizationId: string | null, riskAssessmentId: string) =>
    [...riskControlKeys.lists(organizationId), "for-assessment", riskAssessmentId] as const,
  forHazard: (organizationId: string | null, hazardId: string) =>
    [...riskControlKeys.lists(organizationId), "for-hazard", hazardId] as const,
  details: (organizationId: string | null) =>
    [...riskControlKeys.all(organizationId), "detail"] as const,
  detail: (organizationId: string | null, riskControlId: string) =>
    [...riskControlKeys.details(organizationId), riskControlId] as const,
  activity: (organizationId: string | null, riskControlId: string) =>
    [...riskControlKeys.detail(organizationId, riskControlId), "activity"] as const,
  hazard: (organizationId: string | null, hazardId: string) =>
    [...riskControlKeys.all(organizationId), "hazard", hazardId] as const,
  assessment: (organizationId: string | null, riskAssessmentId: string) =>
    [...riskControlKeys.all(organizationId), "assessment", riskAssessmentId] as const,
};
