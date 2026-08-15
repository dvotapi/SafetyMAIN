import { apiClient } from "@/services/api/client";

import { mapRiskControlDto } from "@/features/risk-controls/mappers/risk-control-mappers";
import type {
  AssignOwnerDto,
  CompleteImplementationDto,
  CompleteReviewDto,
  EvidenceRequestDto,
  MaterializeControlsDto,
  PlanRiskControlDto,
  ProgressDto,
  ReasonVersionDto,
  RiskControlDto,
  ScheduleReviewDto,
  SupersedeDto,
  SuspendDto,
  VerificationRequestDto,
  VersionOnlyDto,
} from "@/features/risk-controls/types/risk-control-dto";
import type { RiskControl } from "@/features/risk-controls/types/risk-control-types";

export async function assignRiskControlOwner(
  riskControlId: string,
  body: AssignOwnerDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/assign-owner`,
    body,
  });
  if (!dto) {
    throw new Error("Empty assign owner response");
  }
  return mapRiskControlDto(dto);
}

export async function planRiskControl(
  riskControlId: string,
  body: PlanRiskControlDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/plan`,
    body,
  });
  if (!dto) {
    throw new Error("Empty plan risk control response");
  }
  return mapRiskControlDto(dto);
}

export async function startRiskControlImplementation(
  riskControlId: string,
  body: VersionOnlyDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/start-implementation`,
    body,
  });
  if (!dto) {
    throw new Error("Empty start implementation response");
  }
  return mapRiskControlDto(dto);
}

export async function updateRiskControlProgress(
  riskControlId: string,
  body: ProgressDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/progress`,
    body,
  });
  if (!dto) {
    throw new Error("Empty update progress response");
  }
  return mapRiskControlDto(dto);
}

export async function addRiskControlEvidence(
  riskControlId: string,
  body: EvidenceRequestDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/evidence`,
    body,
  });
  if (!dto) {
    throw new Error("Empty add evidence response");
  }
  return mapRiskControlDto(dto);
}

export async function completeRiskControlImplementation(
  riskControlId: string,
  body: CompleteImplementationDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/complete-implementation`,
    body,
  });
  if (!dto) {
    throw new Error("Empty complete implementation response");
  }
  return mapRiskControlDto(dto);
}

export async function recordRiskControlVerification(
  riskControlId: string,
  body: VerificationRequestDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/verifications`,
    body,
  });
  if (!dto) {
    throw new Error("Empty record verification response");
  }
  return mapRiskControlDto(dto);
}

export async function scheduleRiskControlReview(
  riskControlId: string,
  body: ScheduleReviewDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/schedule-review`,
    body,
  });
  if (!dto) {
    throw new Error("Empty schedule review response");
  }
  return mapRiskControlDto(dto);
}

export async function completeRiskControlReview(
  riskControlId: string,
  body: CompleteReviewDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/complete-review`,
    body,
  });
  if (!dto) {
    throw new Error("Empty complete review response");
  }
  return mapRiskControlDto(dto);
}

export async function suspendRiskControl(
  riskControlId: string,
  body: SuspendDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/suspend`,
    body,
  });
  if (!dto) {
    throw new Error("Empty suspend response");
  }
  return mapRiskControlDto(dto);
}

export async function resumeRiskControl(
  riskControlId: string,
  body: VersionOnlyDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/resume`,
    body,
  });
  if (!dto) {
    throw new Error("Empty resume response");
  }
  return mapRiskControlDto(dto);
}

export async function supersedeRiskControl(
  riskControlId: string,
  body: SupersedeDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/supersede`,
    body,
  });
  if (!dto) {
    throw new Error("Empty supersede response");
  }
  return mapRiskControlDto(dto);
}

export async function archiveRiskControl(
  riskControlId: string,
  body: ReasonVersionDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/archive`,
    body,
  });
  if (!dto) {
    throw new Error("Empty archive response");
  }
  return mapRiskControlDto(dto);
}

export async function cancelRiskControl(
  riskControlId: string,
  body: ReasonVersionDto,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "POST",
    path: `/api/v1/risk-controls/${riskControlId}/cancel`,
    body,
  });
  if (!dto) {
    throw new Error("Empty cancel response");
  }
  return mapRiskControlDto(dto);
}

export async function materializeRiskControls(
  riskAssessmentId: string,
  body: MaterializeControlsDto,
): Promise<RiskControl[]> {
  const dto = await apiClient.request<{ items: RiskControlDto[] }>({
    method: "POST",
    path: `/api/v1/risk-assessments/${riskAssessmentId}/materialize-controls`,
    body,
  });
  if (!dto) {
    throw new Error("Empty materialize controls response");
  }
  return dto.items.map(mapRiskControlDto);
}
