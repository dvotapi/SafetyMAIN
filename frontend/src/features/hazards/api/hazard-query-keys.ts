import type { HazardListParams } from "@/features/hazards/types/hazard-types";

export const hazardKeys = {
  all: (organizationId: string | null) =>
    ["hazards", organizationId ?? "none"] as const,
  lists: (organizationId: string | null) =>
    [...hazardKeys.all(organizationId), "list"] as const,
  list: (organizationId: string | null, filters: HazardListParams) =>
    [...hazardKeys.lists(organizationId), filters] as const,
  details: (organizationId: string | null) =>
    [...hazardKeys.all(organizationId), "detail"] as const,
  detail: (organizationId: string | null, hazardId: string) =>
    [...hazardKeys.details(organizationId), hazardId] as const,
  relatedRiskAssessments: (organizationId: string | null, hazardId: string) =>
    [
      ...hazardKeys.detail(organizationId, hazardId),
      "risk-assessments",
    ] as const,
  activity: (organizationId: string | null, hazardId: string) =>
    [...hazardKeys.detail(organizationId, hazardId), "activity"] as const,
};
