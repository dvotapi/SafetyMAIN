import { apiClient } from "@/services/api/client";

import {
  mapRiskControlDto,
  mapRiskControlListDto,
} from "@/features/risk-controls/mappers/risk-control-mappers";
import type {
  RiskControlDto,
  RiskControlListDto,
  RiskControlListParams,
} from "@/features/risk-controls/types/risk-control-dto";
import type {
  RiskControl,
  RiskControlActivityItem,
  RiskControlAssessmentSummary,
  RiskControlHazardSummary,
  RiskControlListResult,
} from "@/features/risk-controls/types/risk-control-types";

export async function listRiskControls(
  params: RiskControlListParams,
  signal?: AbortSignal,
): Promise<RiskControlListResult> {
  const query: Record<string, string | number | boolean | undefined> = {
    offset: params.offset ?? 0,
    limit: params.limit ?? 25,
  };
  if (params.status) query.status = params.status;
  if (params.hierarchy_level) query.hierarchy_level = params.hierarchy_level;
  if (params.control_nature) query.control_nature = params.control_nature;
  if (params.hazard_id) query.hazard_id = params.hazard_id;
  if (params.risk_assessment_id) {
    query.risk_assessment_id = params.risk_assessment_id;
  }
  if (params.owner_reference) query.owner_reference = params.owner_reference;
  if (params.latest_effectiveness_result) {
    query.latest_effectiveness_result = params.latest_effectiveness_result;
  }
  if (params.review_due_before)
    query.review_due_before = params.review_due_before;
  if (params.review_due_after) query.review_due_after = params.review_due_after;
  if (params.overdue_only) query.overdue_only = true;
  if (params.awaiting_verification) query.awaiting_verification = true;
  if (params.include_terminal) query.include_terminal = true;
  if (params.search) query.search = params.search;

  const dto = await apiClient.request<RiskControlListDto>({
    method: "GET",
    path: "/api/v1/risk-controls",
    query,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty risk control list response");
  }
  return mapRiskControlListDto(dto);
}

export async function getRiskControl(
  riskControlId: string,
  signal?: AbortSignal,
): Promise<RiskControl> {
  const dto = await apiClient.request<RiskControlDto>({
    method: "GET",
    path: `/api/v1/risk-controls/${riskControlId}`,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty risk control response");
  }
  return mapRiskControlDto(dto);
}

/** RC-local lite reads — must not import Hazard or Risk Assessment internals. */
interface RelatedObjectDtoLite {
  id: string;
  code: string;
  title: string;
  status: string;
}

export async function getHazardForRiskControl(
  hazardId: string,
  signal?: AbortSignal,
): Promise<RiskControlHazardSummary> {
  const dto = await apiClient.request<RelatedObjectDtoLite>({
    method: "GET",
    path: `/api/v1/hazards/${hazardId}`,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty hazard response");
  }
  return { id: dto.id, code: dto.code, title: dto.title, status: dto.status };
}

export async function getAssessmentForRiskControl(
  riskAssessmentId: string,
  signal?: AbortSignal,
): Promise<RiskControlAssessmentSummary> {
  const dto = await apiClient.request<RelatedObjectDtoLite>({
    method: "GET",
    path: `/api/v1/risk-assessments/${riskAssessmentId}`,
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty risk assessment response");
  }
  return { id: dto.id, code: dto.code, title: dto.title, status: dto.status };
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
  "safety.risk_control.created": "Risk control created",
  "safety.risk_control.updated": "Risk control updated",
  "safety.risk_control.owner_assigned": "Owner assigned",
  "safety.risk_control.owner_changed": "Owner changed",
  "safety.risk_control.planned": "Implementation planned",
  "safety.risk_control.implementation_started": "Implementation started",
  "safety.risk_control.progress_updated": "Progress updated",
  "safety.risk_control.evidence_added": "Evidence added",
  "safety.risk_control.implemented": "Implementation completed",
  "safety.risk_control.verification_recorded": "Verification recorded",
  "safety.risk_control.verified_effective": "Verified Effective",
  "safety.risk_control.verified_partially_effective":
    "Verified Partially Effective",
  "safety.risk_control.verified_ineffective": "Verified Ineffective",
  "safety.risk_control.review_scheduled": "Review scheduled",
  "safety.risk_control.review_completed": "Review completed",
  "safety.risk_control.suspended": "Suspended",
  "safety.risk_control.resumed": "Resumed",
  "safety.risk_control.superseded": "Superseded",
  "safety.risk_control.archived": "Archived",
  "safety.risk_control.cancelled": "Cancelled",
  "safety.risk_control.materialized": "Materialized from risk assessment",
};

export async function listRiskControlActivity(
  riskControlId: string,
  signal?: AbortSignal,
): Promise<RiskControlActivityItem[]> {
  const dto = await apiClient.request<AuditEventListDto>({
    method: "GET",
    path: "/api/v1/admin/audit-events",
    query: {
      resource_type: "RISK_CONTROL",
      resource_id: riskControlId,
      // Backend caps audit-event limit at 100.
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
