"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { invalidateHazardRelatedRiskAssessments } from "@/features/risk-assessments/api/invalidate-hazard-related";
import {
  approveRiskAssessment,
  archiveRiskAssessment,
  createRiskAssessment,
  updateRiskAssessment,
} from "@/features/risk-assessments/api/risk-assessment-api";
import { riskAssessmentKeys } from "@/features/risk-assessments/api/risk-assessment-query-keys";
import type {
  ApproveRiskAssessmentDto,
  ArchiveRiskAssessmentDto,
  CreateRiskAssessmentDto,
  RiskAssessment,
  UpdateRiskAssessmentDto,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { useOrganization } from "@/hooks/auth";

function useInvalidateRiskAssessments() {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return {
    queryClient,
    organizationId,
    invalidateLists: () =>
      queryClient.invalidateQueries({
        queryKey: riskAssessmentKeys.lists(organizationId),
      }),
    setDetail: (riskAssessmentId: string, data: RiskAssessment) =>
      queryClient.setQueryData(
        riskAssessmentKeys.detail(organizationId, riskAssessmentId),
        data,
      ),
    invalidateDetail: (riskAssessmentId: string) =>
      queryClient.invalidateQueries({
        queryKey: riskAssessmentKeys.detail(organizationId, riskAssessmentId),
      }),
    invalidateActivity: (riskAssessmentId: string) =>
      queryClient.invalidateQueries({
        queryKey: riskAssessmentKeys.activity(organizationId, riskAssessmentId),
      }),
    invalidateRelatedControls: (riskAssessmentId: string) =>
      queryClient.invalidateQueries({
        queryKey: riskAssessmentKeys.relatedControls(
          organizationId,
          riskAssessmentId,
        ),
      }),
    invalidateHazardRelated: (hazardId?: string) =>
      invalidateHazardRelatedRiskAssessments(queryClient, {
        organizationId,
        ...(hazardId ? { hazardId } : {}),
      }),
  };
}

export function useCreateRiskAssessmentMutation() {
  const { invalidateLists, setDetail, invalidateHazardRelated } =
    useInvalidateRiskAssessments();
  return useMutation({
    mutationFn: (body: CreateRiskAssessmentDto) => createRiskAssessment(body),
    onSuccess: (assessment) => {
      setDetail(assessment.id, assessment);
      void invalidateLists();
      void invalidateHazardRelated(assessment.hazardId);
    },
  });
}

export function useUpdateRiskAssessmentMutation(riskAssessmentId: string) {
  const {
    invalidateLists,
    setDetail,
    invalidateDetail,
    invalidateActivity,
    invalidateRelatedControls,
    invalidateHazardRelated,
  } = useInvalidateRiskAssessments();
  return useMutation({
    mutationFn: (body: UpdateRiskAssessmentDto) =>
      updateRiskAssessment(riskAssessmentId, body),
    onSuccess: (assessment) => {
      setDetail(assessment.id, assessment);
      void invalidateLists();
      void invalidateDetail(assessment.id);
      void invalidateActivity(assessment.id);
      void invalidateRelatedControls(assessment.id);
      void invalidateHazardRelated(assessment.hazardId);
    },
  });
}

export function useApproveRiskAssessmentMutation(riskAssessmentId: string) {
  const {
    queryClient,
    organizationId,
    invalidateLists,
    setDetail,
    invalidateDetail,
    invalidateActivity,
    invalidateRelatedControls,
    invalidateHazardRelated,
  } = useInvalidateRiskAssessments();
  return useMutation({
    mutationFn: (body: ApproveRiskAssessmentDto) =>
      approveRiskAssessment(riskAssessmentId, body),
    onSuccess: (assessment) => {
      setDetail(assessment.id, assessment);
      void invalidateLists();
      void invalidateDetail(assessment.id);
      void invalidateActivity(assessment.id);
      void invalidateRelatedControls(assessment.id);
      // Superseded peers are refreshed via list/detail invalidation — do not guess IDs.
      void queryClient.invalidateQueries({
        queryKey: riskAssessmentKeys.details(organizationId),
      });
      void invalidateHazardRelated(assessment.hazardId);
    },
  });
}

export function useArchiveRiskAssessmentMutation(riskAssessmentId: string) {
  const {
    invalidateLists,
    setDetail,
    invalidateDetail,
    invalidateActivity,
    invalidateHazardRelated,
  } = useInvalidateRiskAssessments();
  return useMutation({
    mutationFn: (body: ArchiveRiskAssessmentDto) =>
      archiveRiskAssessment(riskAssessmentId, body),
    onSuccess: (assessment) => {
      setDetail(assessment.id, assessment);
      void invalidateLists();
      void invalidateDetail(assessment.id);
      void invalidateActivity(assessment.id);
      void invalidateHazardRelated(assessment.hazardId);
    },
  });
}
