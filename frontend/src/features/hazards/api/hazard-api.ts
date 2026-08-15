import { apiClient } from "@/services/api/client";

import {
  mapHazardDto,
  mapHazardListDto,
} from "@/features/hazards/mappers/hazard-mappers";
import type {
  CreateHazardDto,
  Hazard,
  HazardActivityItem,
  HazardDto,
  HazardListDto,
  HazardListParams,
  HazardListResult,
  RiskAssessmentSummary,
  UpdateHazardDto,
} from "@/features/hazards/types/hazard-types";

function riskLabel(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const level = record["level"] ?? record["score"] ?? record["rating"];
    if (typeof level === "string" || typeof level === "number") {
      return String(level);
    }
  }
  return null;
}

export async function listHazards(
  params: HazardListParams,
  signal?: AbortSignal,
): Promise<HazardListResult> {
  const query: Record<string, string | number | boolean | undefined | null> = {
    offset: params.offset ?? 0,
    limit: params.limit ?? 50,
    include_archived: params.include_archived ?? false,
  };
  if (params.status) query.status = params.status;
  if (params.category) query.category = params.category;
  if (params.safety_direction) query.safety_direction = params.safety_direction;
  if (params.source) query.source = params.source;
  if (params.affected_subject) query.affected_subject = params.affected_subject;
  if (params.search) query.search = params.search;
  if (params.identified_from) query.identified_from = params.identified_from;
  if (params.identified_to) query.identified_to = params.identified_to;
  if (params.created_from) query.created_from = params.created_from;
  if (params.created_to) query.created_to = params.created_to;

  const dto = await apiClient.request<HazardListDto>({
    method: "GET",
    path: "/api/v1/hazards",
    query,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty hazard list response");
  }
  return mapHazardListDto(dto);
}

export async function getHazard(
  hazardId: string,
  signal?: AbortSignal,
): Promise<Hazard> {
  const dto = await apiClient.request<HazardDto>({
    method: "GET",
    path: `/api/v1/hazards/${hazardId}`,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty hazard response");
  }
  return mapHazardDto(dto);
}

export async function createHazard(body: CreateHazardDto): Promise<Hazard> {
  const dto = await apiClient.request<HazardDto>({
    method: "POST",
    path: "/api/v1/hazards",
    body,
  });
  if (!dto) {
    throw new Error("Empty create hazard response");
  }
  return mapHazardDto(dto);
}

export async function updateHazard(
  hazardId: string,
  body: UpdateHazardDto,
): Promise<Hazard> {
  const dto = await apiClient.request<HazardDto>({
    method: "PATCH",
    path: `/api/v1/hazards/${hazardId}`,
    body,
  });
  if (!dto) {
    throw new Error("Empty update hazard response");
  }
  return mapHazardDto(dto);
}

export async function activateHazard(
  hazardId: string,
  expectedVersion: number,
): Promise<Hazard> {
  const dto = await apiClient.request<HazardDto>({
    method: "POST",
    path: `/api/v1/hazards/${hazardId}/activate`,
    body: { expected_version: expectedVersion },
  });
  if (!dto) {
    throw new Error("Empty activate hazard response");
  }
  return mapHazardDto(dto);
}

export async function archiveHazard(
  hazardId: string,
  expectedVersion: number,
  reason: string,
): Promise<Hazard> {
  const dto = await apiClient.request<HazardDto>({
    method: "POST",
    path: `/api/v1/hazards/${hazardId}/archive`,
    body: { expected_version: expectedVersion, reason },
  });
  if (!dto) {
    throw new Error("Empty archive hazard response");
  }
  return mapHazardDto(dto);
}

export async function restoreHazard(
  hazardId: string,
  expectedVersion: number,
  reason: string,
): Promise<Hazard> {
  const dto = await apiClient.request<HazardDto>({
    method: "POST",
    path: `/api/v1/hazards/${hazardId}/restore`,
    body: { expected_version: expectedVersion, reason },
  });
  if (!dto) {
    throw new Error("Empty restore hazard response");
  }
  return mapHazardDto(dto);
}

interface RiskAssessmentListDto {
  items: Array<{
    id: string;
    code: string;
    title: string;
    status: string;
    assessment_profile: string;
    inherent_risk: unknown;
    residual_risk: unknown;
    approved_at: string | null;
    updated_at: string;
  }>;
  pagination: { total: number; offset: number; limit: number };
}

export async function listRelatedRiskAssessments(
  hazardId: string,
  signal?: AbortSignal,
): Promise<RiskAssessmentSummary[]> {
  const dto = await apiClient.request<RiskAssessmentListDto>({
    method: "GET",
    path: "/api/v1/risk-assessments",
    query: {
      hazard_id: hazardId,
      limit: 50,
      offset: 0,
      include_archived: true,
      include_superseded: true,
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
    assessmentProfile: item.assessment_profile,
    inherentRiskLabel: riskLabel(item.inherent_risk),
    residualRiskLabel: riskLabel(item.residual_risk),
    approvedAt: item.approved_at,
    updatedAt: item.updated_at,
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
  "safety.hazard.created": "Hazard created",
  "safety.hazard.updated": "Hazard updated",
  "safety.hazard.activated": "Hazard activated",
  "safety.hazard.archived": "Hazard archived",
  "safety.hazard.restored": "Hazard restored",
};

export async function listHazardActivity(
  hazardId: string,
  signal?: AbortSignal,
): Promise<HazardActivityItem[]> {
  const dto = await apiClient.request<AuditEventListDto>({
    method: "GET",
    path: "/api/v1/admin/audit-events",
    query: {
      resource_type: "HAZARD",
      resource_id: hazardId,
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
