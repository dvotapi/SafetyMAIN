"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { invalidateAssessmentRelatedControls } from "@/features/risk-controls/api/invalidate-assessment-related";
import {
  addRiskControlEvidence,
  archiveRiskControl,
  assignRiskControlOwner,
  cancelRiskControl,
  completeRiskControlImplementation,
  completeRiskControlReview,
  materializeRiskControls,
  planRiskControl,
  recordRiskControlVerification,
  resumeRiskControl,
  scheduleRiskControlReview,
  startRiskControlImplementation,
  supersedeRiskControl,
  suspendRiskControl,
  updateRiskControlProgress,
} from "@/features/risk-controls/api/risk-control-commands";
import { riskControlKeys } from "@/features/risk-controls/api/risk-control-query-keys";
import type {
  AssignOwnerDto,
  CompleteImplementationDto,
  CompleteReviewDto,
  EvidenceRequestDto,
  MaterializeControlsDto,
  PlanRiskControlDto,
  ProgressDto,
  ReasonVersionDto,
  ScheduleReviewDto,
  SupersedeDto,
  SuspendDto,
  VerificationRequestDto,
  VersionOnlyDto,
} from "@/features/risk-controls/types/risk-control-dto";
import type { RiskControl } from "@/features/risk-controls/types/risk-control-types";
import { useOrganization } from "@/hooks/auth";

function useInvalidateRiskControls() {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return {
    queryClient,
    organizationId,
    setDetail: (id: string, data: RiskControl) =>
      queryClient.setQueryData(
        riskControlKeys.detail(organizationId, id),
        data,
      ),
    invalidateLists: () =>
      queryClient.invalidateQueries({
        queryKey: riskControlKeys.lists(organizationId),
      }),
    invalidateDetail: (id: string) =>
      queryClient.invalidateQueries({
        queryKey: riskControlKeys.detail(organizationId, id),
      }),
    invalidateActivity: (id: string) =>
      queryClient.invalidateQueries({
        queryKey: riskControlKeys.activity(organizationId, id),
      }),
    invalidateAssessmentRelated: (riskAssessmentId?: string) =>
      riskAssessmentId
        ? invalidateAssessmentRelatedControls(queryClient, {
            organizationId,
            riskAssessmentId,
          })
        : Promise.resolve(),
  };
}

/**
 * Every lifecycle command mutation shares the same onSuccess sequence
 * (cache the new detail, invalidate lists/activity/related-assessment) and
 * differs only in the command function and its request DTO type.
 */
function useRiskControlLifecycleMutation<TDto>(
  riskControlId: string,
  commandFn: (id: string, body: TDto) => Promise<RiskControl>,
) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: TDto) => commandFn(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useAssignRiskControlOwnerMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<AssignOwnerDto>(
    riskControlId,
    assignRiskControlOwner,
  );
}

export function usePlanRiskControlMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<PlanRiskControlDto>(
    riskControlId,
    planRiskControl,
  );
}

export function useStartRiskControlImplementationMutation(
  riskControlId: string,
) {
  return useRiskControlLifecycleMutation<VersionOnlyDto>(
    riskControlId,
    startRiskControlImplementation,
  );
}

export function useUpdateRiskControlProgressMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<ProgressDto>(
    riskControlId,
    updateRiskControlProgress,
  );
}

export function useAddRiskControlEvidenceMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<EvidenceRequestDto>(
    riskControlId,
    addRiskControlEvidence,
  );
}

export function useCompleteRiskControlImplementationMutation(
  riskControlId: string,
) {
  return useRiskControlLifecycleMutation<CompleteImplementationDto>(
    riskControlId,
    completeRiskControlImplementation,
  );
}

export function useRecordRiskControlVerificationMutation(
  riskControlId: string,
) {
  return useRiskControlLifecycleMutation<VerificationRequestDto>(
    riskControlId,
    recordRiskControlVerification,
  );
}

export function useScheduleRiskControlReviewMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<ScheduleReviewDto>(
    riskControlId,
    scheduleRiskControlReview,
  );
}

export function useCompleteRiskControlReviewMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<CompleteReviewDto>(
    riskControlId,
    completeRiskControlReview,
  );
}

export function useSuspendRiskControlMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<SuspendDto>(
    riskControlId,
    suspendRiskControl,
  );
}

export function useResumeRiskControlMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<VersionOnlyDto>(
    riskControlId,
    resumeRiskControl,
  );
}

export function useSupersedeRiskControlMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<SupersedeDto>(
    riskControlId,
    supersedeRiskControl,
  );
}

export function useArchiveRiskControlMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<ReasonVersionDto>(
    riskControlId,
    archiveRiskControl,
  );
}

export function useCancelRiskControlMutation(riskControlId: string) {
  return useRiskControlLifecycleMutation<ReasonVersionDto>(
    riskControlId,
    cancelRiskControl,
  );
}

export function useMaterializeRiskControlsMutation(riskAssessmentId: string) {
  const { setDetail, invalidateLists, invalidateAssessmentRelated } =
    useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: MaterializeControlsDto) =>
      materializeRiskControls(riskAssessmentId, body),
    onSuccess: (controls) => {
      for (const control of controls) {
        setDetail(control.id, control);
      }
      void invalidateLists();
      void invalidateAssessmentRelated(riskAssessmentId);
    },
  });
}
