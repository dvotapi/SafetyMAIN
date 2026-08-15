"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getHazard,
  listHazardActivity,
  listHazards,
  listRelatedRiskAssessments,
} from "@/features/hazards/api/hazard-api";
import { hazardKeys } from "@/features/hazards/api/hazard-query-keys";
import type { HazardListParams } from "@/features/hazards/types/hazard-types";
import { useOrganization } from "@/hooks/auth";

export function useHazardListQuery(filters: HazardListParams, enabled = true) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: hazardKeys.list(organizationId, filters),
    queryFn: ({ signal }) => listHazards(filters, signal),
    enabled: enabled && Boolean(organizationId),
  });
}

export function useHazardDetailQuery(hazardId: string, enabled = true) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: hazardKeys.detail(organizationId, hazardId),
    queryFn: ({ signal }) => getHazard(hazardId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(hazardId),
  });
}

export function useRelatedRiskAssessmentsQuery(
  hazardId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: hazardKeys.relatedRiskAssessments(organizationId, hazardId),
    queryFn: ({ signal }) => listRelatedRiskAssessments(hazardId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(hazardId),
  });
}

export function useHazardActivityQuery(hazardId: string, enabled = true) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: hazardKeys.activity(organizationId, hazardId),
    queryFn: ({ signal }) => listHazardActivity(hazardId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(hazardId),
  });
}
