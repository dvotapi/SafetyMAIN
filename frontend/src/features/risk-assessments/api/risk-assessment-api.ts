import { apiClient } from "@/services/api/client";

import {
  mapRiskAssessmentDto,
  mapRiskAssessmentListDto,
} from "@/features/risk-assessments/mappers/risk-assessment-mappers";
import type {
  ApproveRiskAssessmentDto,
  ArchiveRiskAssessmentDto,
  CreateRiskAssessmentDto,
  RelatedRiskControlSummary,
  RiskAssessment,
  RiskAssessmentActivityItem,
  RiskAssessmentDto,
  RiskAssessmentHazardSummary,
  RiskAssessmentListDto,
  RiskAssessmentListParams,
  RiskAssessmentListResult,
  UpdateRiskAssessmentDto,
} from "@/features/risk-assessments/types/risk-assessment-types";

export async function listRiskAssessments(
  params: RiskAssessmentListParams,
  signal?: AbortSignal,
): Promise<RiskAssessmentListResult> {
  const query: Record<string, string | number | boolean | undefined | null> = {
    offset: params.offset ?? 0,
    limit: params.limit ?? 50,
    include_archived: params.include_archived ?? false,
    include_superseded: params.include_superseded ?? true,
  };
  if (params.hazard_id) query.hazard_id = params.hazard_id;
  if (params.status) query.status = params.status;
  if (params.assessment_profile) {
    query.assessment_profile = params.assessment_profile;
  }
  if (params.assessed_object_type) {
    query.assessed_object_type = params.assessed_object_type;
  }
  if (params.search) query.search = params.search;
  if (params.created_from) query.created_from = params.created_from;
  if (params.created_to) query.created_to = params.created_to;

  const dto = await apiClient.request<RiskAssessmentListDto>({
    method: "GET",
    path: "/api/v1/risk-assessments",
    query,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty risk assessment list response");
  }
  return mapRiskAssessmentListDto(dto);
}

export async function getRiskAssessment(
  riskAssessmentId: string,
  signal?: AbortSignal,
): Promise<RiskAssessment> {
  const dto = await apiClient.request<RiskAssessmentDto>({
    method: "GET",
    path: `/api/v1/risk-assessments/${riskAssessmentId}`,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty risk assessment response");
  }
  return mapRiskAssessmentDto(dto);
}

export async function createRiskAssessment(
  body: CreateRiskAssessmentDto,
): Promise<RiskAssessment> {
  const dto = await apiClient.request<RiskAssessmentDto>({
    method: "POST",
    path: "/api/v1/risk-assessments",
    body,
  });
  if (!dto) {
    throw new Error("Empty create risk assessment response");
  }
  return mapRiskAssessmentDto(dto);
}

export async function updateRiskAssessment(
  riskAssessmentId: string,
  body: UpdateRiskAssessmentDto,
): Promise<RiskAssessment> {
  const dto = await apiClient.request<RiskAssessmentDto>({
    method: "PATCH",
    path: `/api/v1/risk-assessments/${riskAssessmentId}`,
    body,
  });
  if (!dto) {
    throw new Error("Empty update risk assessment response");
  }
  return mapRiskAssessmentDto(dto);
}

export async function approveRiskAssessment(
  riskAssessmentId: string,
  body: ApproveRiskAssessmentDto,
): Promise<RiskAssessment> {
  const dto = await apiClient.request<RiskAssessmentDto>({
    method: "POST",
    path: `/api/v1/risk-assessments/${riskAssessmentId}/approve`,
    body,
  });
  if (!dto) {
    throw new Error("Empty approve risk assessment response");
  }
  return mapRiskAssessmentDto(dto);
}

export async function archiveRiskAssessment(
  riskAssessmentId: string,
  body: ArchiveRiskAssessmentDto,
): Promise<RiskAssessment> {
  const dto = await apiClient.request<RiskAssessmentDto>({
    method: "POST",
    path: `/api/v1/risk-assessments/${riskAssessmentId}/archive`,
    body,
  });
  if (!dto) {
    throw new Error("Empty archive risk assessment response");
  }
  return mapRiskAssessmentDto(dto);
}

/** RA-local Hazard access — does not import Hazard feature internals. */
interface HazardDtoLite {
  id: string;
  code: string;
  title: string;
  status: string;
}

interface HazardListDtoLite {
  items: HazardDtoLite[];
  pagination: { total: number; offset: number; limit: number };
}

export async function listHazardsForRiskAssessment(
  params: { search?: string; limit?: number; offset?: number; status?: string },
  signal?: AbortSignal,
): Promise<RiskAssessmentHazardSummary[]> {
  const dto = await apiClient.request<HazardListDtoLite>({
    method: "GET",
    path: "/api/v1/hazards",
    query: {
      offset: params.offset ?? 0,
      limit: params.limit ?? 50,
      include_archived: false,
      ...(params.search ? { search: params.search } : {}),
      ...(params.status ? { status: params.status } : {}),
    },
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    return [];
  }
  return dto.items.map((item) => ({
    id: item.id,
    code: item.code,
    title: item.title,
    status: item.status,
  }));
}

export async function getHazardForRiskAssessment(
  hazardId: string,
  signal?: AbortSignal,
): Promise<RiskAssessmentHazardSummary> {
  const dto = await apiClient.request<HazardDtoLite>({
    method: "GET",
    path: `/api/v1/hazards/${hazardId}`,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty hazard response");
  }
  return {
    id: dto.id,
    code: dto.code,
    title: dto.title,
    status: dto.status,
  };
}

interface RiskControlOwnerDto {
  owner_type: string;
  owner_reference: string;
  display_name_snapshot: string;
  assigned_at: string;
  assigned_by: string;
}

interface RiskControlListDto {
  items: Array<{
    id: string;
    code: string;
    title: string;
    hierarchy_level: string;
    lifecycle_status: string;
    owner: RiskControlOwnerDto | null;
    latest_effectiveness_result: string | null;
    next_review_date: string | null;
  }>;
  pagination: { total: number; offset: number; limit: number };
}

/** Maps backend owner dict to a display label. */
export function mapRiskControlOwnerLabel(
  owner: RiskControlOwnerDto | null | undefined,
): string | null {
  if (!owner) {
    return null;
  }
  const snapshot = owner.display_name_snapshot?.trim();
  if (snapshot) {
    return snapshot;
  }
  const reference = owner.owner_reference?.trim();
  return reference || null;
}

export async function listRelatedRiskControls(
  riskAssessmentId: string,
  signal?: AbortSignal,
): Promise<RelatedRiskControlSummary[]> {
  const dto = await apiClient.request<RiskControlListDto>({
    method: "GET",
    path: "/api/v1/risk-controls",
    query: {
      risk_assessment_id: riskAssessmentId,
      include_terminal: true,
      offset: 0,
      limit: 50,
    },
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    return [];
  }
  return dto.items.map((item) => ({
    id: item.id,
    code: item.code,
    title: item.title,
    hierarchyLevel: item.hierarchy_level,
    lifecycleStatus: item.lifecycle_status,
    ownerLabel: mapRiskControlOwnerLabel(item.owner),
    latestEffectivenessResult: item.latest_effectiveness_result,
    nextReviewDate: item.next_review_date,
  }));
}

interface AuditEventListDto {
  items: Array<{
    id: string;
    actor_user_id: string | null;
    event_name: string;
    action: string;
    outcome: string;
    occurred_at: string;
  }>;
}

const ACTIVITY_TITLES: Record<string, string> = {
  "safety.risk.created": "Оценка риска создана",
  "safety.risk.updated": "Оценка риска изменена",
  "safety.risk.approved": "Оценка риска утверждена",
  "safety.risk.superseded": "Оценка риска замещена",
  "safety.risk.archived": "Оценка риска архивирована",
};

export async function listRiskAssessmentActivity(
  riskAssessmentId: string,
  signal?: AbortSignal,
): Promise<RiskAssessmentActivityItem[]> {
  const dto = await apiClient.request<AuditEventListDto>({
    method: "GET",
    path: "/api/v1/admin/audit-events",
    query: {
      resource_type: "RISK",
      resource_id: riskAssessmentId,
      limit: 50,
      offset: 0,
    },
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    return [];
  }
  return dto.items.map((item) => ({
    id: item.id,
    title: ACTIVITY_TITLES[item.event_name] ?? item.event_name,
    occurredAt: item.occurred_at,
    actorUserId: item.actor_user_id,
    action: item.action,
    outcome: item.outcome,
    eventName: item.event_name,
  }));
}
