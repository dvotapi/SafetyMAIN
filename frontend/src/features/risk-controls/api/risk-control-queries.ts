"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getAssessmentForRiskControl,
  getHazardForRiskControl,
  getRiskControl,
  listRiskControlActivity,
  listRiskControls,
} from "@/features/risk-controls/api/risk-control-api";
import { riskControlKeys } from "@/features/risk-controls/api/risk-control-query-keys";
import type { RiskControlListParams } from "@/features/risk-controls/types/risk-control-dto";
import { useOrganization } from "@/hooks/auth";

export function useRiskControlListQuery(
  filters: RiskControlListParams,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskControlKeys.list(organizationId, filters),
    queryFn: ({ signal }) => listRiskControls(filters, signal),
    enabled: enabled && Boolean(organizationId),
  });
}

export function useRiskControlDetailQuery(
  riskControlId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskControlKeys.detail(organizationId, riskControlId),
    queryFn: ({ signal }) => getRiskControl(riskControlId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(riskControlId),
  });
}

export function useRiskControlActivityQuery(
  riskControlId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskControlKeys.activity(organizationId, riskControlId),
    queryFn: ({ signal }) => listRiskControlActivity(riskControlId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(riskControlId),
  });
}

export function useRiskControlHazardQuery(hazardId: string, enabled = true) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskControlKeys.hazard(organizationId, hazardId),
    queryFn: ({ signal }) => getHazardForRiskControl(hazardId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(hazardId),
    retry: false,
  });
}

export function useRiskControlAssessmentQuery(
  riskAssessmentId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: riskControlKeys.assessment(organizationId, riskAssessmentId),
    queryFn: ({ signal }) =>
      getAssessmentForRiskControl(riskAssessmentId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(riskAssessmentId),
    retry: false,
  });
}
