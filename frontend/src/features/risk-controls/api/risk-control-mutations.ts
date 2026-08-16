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
      invalidateAssessmentRelatedControls(queryClient, {
        organizationId,
        ...(riskAssessmentId ? { riskAssessmentId } : {}),
      }),
  };
}

export function useAssignRiskControlOwnerMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: AssignOwnerDto) =>
      assignRiskControlOwner(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function usePlanRiskControlMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: PlanRiskControlDto) =>
      planRiskControl(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useStartRiskControlImplementationMutation(
  riskControlId: string,
) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: VersionOnlyDto) =>
      startRiskControlImplementation(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useUpdateRiskControlProgressMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: ProgressDto) =>
      updateRiskControlProgress(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useAddRiskControlEvidenceMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: EvidenceRequestDto) =>
      addRiskControlEvidence(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useCompleteRiskControlImplementationMutation(
  riskControlId: string,
) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: CompleteImplementationDto) =>
      completeRiskControlImplementation(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useRecordRiskControlVerificationMutation(
  riskControlId: string,
) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: VerificationRequestDto) =>
      recordRiskControlVerification(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useScheduleRiskControlReviewMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: ScheduleReviewDto) =>
      scheduleRiskControlReview(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useCompleteRiskControlReviewMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: CompleteReviewDto) =>
      completeRiskControlReview(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useSuspendRiskControlMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: SuspendDto) => suspendRiskControl(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useResumeRiskControlMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: VersionOnlyDto) =>
      resumeRiskControl(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useSupersedeRiskControlMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: SupersedeDto) =>
      supersedeRiskControl(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useArchiveRiskControlMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: ReasonVersionDto) =>
      archiveRiskControl(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
}

export function useCancelRiskControlMutation(riskControlId: string) {
  const {
    setDetail,
    invalidateLists,
    invalidateActivity,
    invalidateAssessmentRelated,
  } = useInvalidateRiskControls();
  return useMutation({
    mutationFn: (body: ReasonVersionDto) =>
      cancelRiskControl(riskControlId, body),
    onSuccess: (control) => {
      setDetail(control.id, control);
      void invalidateLists();
      void invalidateActivity(control.id);
      void invalidateAssessmentRelated(control.riskAssessmentId ?? undefined);
    },
  });
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
