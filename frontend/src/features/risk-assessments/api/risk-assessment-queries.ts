"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getHazardForRiskAssessment,
  getRiskAssessment,
  listHazardsForRiskAssessment,
  listRelatedRiskControls,
  listRiskAssessmentActivity,
  listRiskAssessments,
} from "@/features/risk-assessments/api/risk-assessment-api";
import { riskAssessmentKeys } from "@/features/risk-assessments/api/risk-assessment-query-keys";
import type { RiskAssessmentListParams } from "@/features/risk-assessments/types/risk-assessment-types";
import { useOrganization } from "@/hooks/auth";

export function useRiskAssessmentListQuery(
  filters: RiskAssessmentListParams,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskAssessmentKeys.list(organizationId, filters),
    queryFn: ({ signal }) => listRiskAssessments(filters, signal),
    enabled: enabled && Boolean(organizationId),
  });
}

export function useRiskAssessmentDetailQuery(
  riskAssessmentId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskAssessmentKeys.detail(organizationId, riskAssessmentId),
    queryFn: ({ signal }) => getRiskAssessment(riskAssessmentId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(riskAssessmentId),
  });
}

export function useRelatedRiskControlsQuery(
  riskAssessmentId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskAssessmentKeys.relatedControls(
      organizationId,
      riskAssessmentId,
    ),
    queryFn: ({ signal }) => listRelatedRiskControls(riskAssessmentId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(riskAssessmentId),
  });
}

export function useRiskAssessmentActivityQuery(
  riskAssessmentId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskAssessmentKeys.activity(organizationId, riskAssessmentId),
    queryFn: ({ signal }) =>
      listRiskAssessmentActivity(riskAssessmentId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(riskAssessmentId),
  });
}

export function useRiskAssessmentHazardQuery(hazardId: string, enabled = true) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: [
      ...riskAssessmentKeys.all(organizationId),
      "hazard",
      hazardId,
    ] as const,
    queryFn: ({ signal }) => getHazardForRiskAssessment(hazardId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(hazardId),
  });
}

export function useRiskAssessmentHazardOptionsQuery(
  search: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: [
      ...riskAssessmentKeys.all(organizationId),
      "hazard-options",
      search,
    ] as const,
    queryFn: ({ signal }) => {
      const params: {
        search?: string;
        status?: string;
        limit?: number;
      } = { status: "active", limit: 50 };
      if (search.trim()) {
        params.search = search.trim();
      }
      return listHazardsForRiskAssessment(params, signal);
    },
    enabled: enabled && Boolean(organizationId),
  });
}
