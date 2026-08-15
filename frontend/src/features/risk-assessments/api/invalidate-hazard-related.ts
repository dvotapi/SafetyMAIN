import type { Query, QueryClient } from "@tanstack/react-query";

/**
 * Boundary-safe invalidation for Hazard-owned related Risk Assessment queries.
 *
 * Keep in sync with Hazard feature key shape (do not import Hazard internals):
 *   ["hazards", organizationId ?? "none", "detail", hazardId, "risk-assessments"]
 */
export const HAZARD_RELATED_RISK_ASSESSMENTS_SUFFIX =
  "risk-assessments" as const;

/** Matches Hazard `hazardKeys.all(organizationId)` org segment. */
export function hazardQueryOrganizationSegment(
  organizationId: string | null | undefined,
): string {
  return organizationId ?? "none";
}

export function isHazardRelatedRiskAssessmentsQueryKey(
  queryKey: readonly unknown[],
  options?: {
    organizationId?: string | null;
    hazardId?: string;
  },
): boolean {
  if (queryKey.length < 5) {
    return false;
  }
  if (queryKey[0] !== "hazards") {
    return false;
  }
  if (queryKey[2] !== "detail") {
    return false;
  }
  if (queryKey[4] !== HAZARD_RELATED_RISK_ASSESSMENTS_SUFFIX) {
    return false;
  }

  // Always scope to one org segment. null/undefined → only the "none" bucket.
  const orgSegment = hazardQueryOrganizationSegment(options?.organizationId);
  if (queryKey[1] !== orgSegment) {
    return false;
  }

  if (options?.hazardId != null && queryKey[3] !== options.hazardId) {
    return false;
  }
  return true;
}

export function hazardRelatedRiskAssessmentsPredicate(options?: {
  organizationId?: string | null;
  hazardId?: string;
}) {
  return (query: Query) =>
    isHazardRelatedRiskAssessmentsQueryKey(query.queryKey, options);
}

export async function invalidateHazardRelatedRiskAssessments(
  queryClient: QueryClient,
  options?: {
    organizationId?: string | null;
    hazardId?: string;
  },
): Promise<void> {
  await queryClient.invalidateQueries({
    predicate: hazardRelatedRiskAssessmentsPredicate(options),
  });
}
