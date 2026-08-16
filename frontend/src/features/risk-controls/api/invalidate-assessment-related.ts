import type { Query, QueryClient } from "@tanstack/react-query";

/**
 * Boundary-safe invalidation of Risk Assessment-owned related-control queries.
 *
 * Keep in sync with the Risk Assessment key shape (do not import its internals):
 *   ["risk-assessments", organizationId ?? "none", "detail", id, "related-controls"]
 */
export const ASSESSMENT_RELATED_CONTROLS_SUFFIX = "related-controls" as const;

/** Matches Risk Assessment `riskAssessmentKeys.all(organizationId)` org segment. */
export function assessmentQueryOrganizationSegment(
  organizationId: string | null | undefined,
): string {
  return organizationId ?? "none";
}

export function isAssessmentRelatedControlsQueryKey(
  queryKey: readonly unknown[],
  options?: {
    organizationId?: string | null;
    riskAssessmentId?: string;
  },
): boolean {
  if (queryKey.length < 5) {
    return false;
  }
  if (queryKey[0] !== "risk-assessments") {
    return false;
  }
  if (queryKey[2] !== "detail") {
    return false;
  }
  if (queryKey[4] !== ASSESSMENT_RELATED_CONTROLS_SUFFIX) {
    return false;
  }

  // Always scope to one org segment. null/undefined → only the "none" bucket.
  const orgSegment = assessmentQueryOrganizationSegment(
    options?.organizationId,
  );
  if (queryKey[1] !== orgSegment) {
    return false;
  }

  if (
    options?.riskAssessmentId != null &&
    queryKey[3] !== options.riskAssessmentId
  ) {
    return false;
  }
  return true;
}

export function assessmentRelatedControlsPredicate(options?: {
  organizationId?: string | null;
  riskAssessmentId?: string;
}) {
  return (query: Query) =>
    isAssessmentRelatedControlsQueryKey(query.queryKey, options);
}

export async function invalidateAssessmentRelatedControls(
  queryClient: QueryClient,
  options?: {
    organizationId?: string | null;
    riskAssessmentId?: string;
  },
): Promise<void> {
  await queryClient.invalidateQueries({
    predicate: assessmentRelatedControlsPredicate(options),
  });
}
