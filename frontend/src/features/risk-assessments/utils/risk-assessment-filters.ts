import type {
  AssessmentProfileDto,
  RiskAssessmentListParams,
  RiskAssessmentStatusDto,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { ASSESSED_OBJECT_TYPES } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import { listAssessmentProfileCodes } from "@/features/risk-assessments/utils/assessment-profiles";

export interface RiskAssessmentRegistryUrlState {
  search: string;
  status: RiskAssessmentStatusDto | "";
  assessmentProfile: AssessmentProfileDto | "";
  hazardId: string;
  assessedObjectType: (typeof ASSESSED_OBJECT_TYPES)[number] | "";
  includeArchived: boolean;
  includeSuperseded: boolean;
  createdFrom: string;
  createdTo: string;
  page: number;
  pageSize: number;
}

export const DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE: RiskAssessmentRegistryUrlState =
  {
    search: "",
    status: "",
    assessmentProfile: "",
    hazardId: "",
    assessedObjectType: "",
    includeArchived: false,
    includeSuperseded: true,
    createdFrom: "",
    createdTo: "",
    page: 1,
    pageSize: 25,
  };

const STATUSES: readonly RiskAssessmentStatusDto[] = [
  "draft",
  "under_review",
  "approved",
  "superseded",
  "archived",
];

function parseEnum<T extends string>(
  value: string | null,
  allowed: readonly T[],
): T | "" {
  if (!value) {
    return "";
  }
  return (allowed as readonly string[]).includes(value) ? (value as T) : "";
}

function parsePositiveInt(value: string | null, fallback: number): number {
  if (!value) {
    return fallback;
  }
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

export function parseRiskAssessmentRegistrySearchParams(
  params: URLSearchParams,
): RiskAssessmentRegistryUrlState {
  const pageSize = Math.min(
    200,
    Math.max(
      1,
      parsePositiveInt(
        params.get("pageSize"),
        DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE.pageSize,
      ),
    ),
  );
  const includeSupersededParam = params.get("includeSuperseded");
  return {
    search: params.get("search")?.trim() ?? "",
    status: parseEnum(params.get("status"), STATUSES),
    assessmentProfile: parseEnum(
      params.get("assessmentProfile"),
      listAssessmentProfileCodes(),
    ),
    hazardId: params.get("hazardId")?.trim() ?? "",
    assessedObjectType: parseEnum(
      params.get("assessedObjectType"),
      ASSESSED_OBJECT_TYPES,
    ),
    includeArchived: params.get("includeArchived") === "true",
    includeSuperseded:
      includeSupersededParam === null
        ? DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE.includeSuperseded
        : includeSupersededParam === "true",
    createdFrom: params.get("createdFrom")?.trim() ?? "",
    createdTo: params.get("createdTo")?.trim() ?? "",
    page: parsePositiveInt(params.get("page"), 1),
    pageSize,
  };
}

export function serializeRiskAssessmentRegistrySearchParams(
  state: RiskAssessmentRegistryUrlState,
): URLSearchParams {
  const params = new URLSearchParams();
  if (state.search) {
    params.set("search", state.search);
  }
  if (state.status) {
    params.set("status", state.status);
  }
  if (state.assessmentProfile) {
    params.set("assessmentProfile", state.assessmentProfile);
  }
  if (state.hazardId) {
    params.set("hazardId", state.hazardId);
  }
  if (state.assessedObjectType) {
    params.set("assessedObjectType", state.assessedObjectType);
  }
  if (state.includeArchived) {
    params.set("includeArchived", "true");
  }
  if (
    state.includeSuperseded !==
    DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE.includeSuperseded
  ) {
    params.set("includeSuperseded", String(state.includeSuperseded));
  }
  if (state.createdFrom) {
    params.set("createdFrom", state.createdFrom);
  }
  if (state.createdTo) {
    params.set("createdTo", state.createdTo);
  }
  if (state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.pageSize !== DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE.pageSize) {
    params.set("pageSize", String(state.pageSize));
  }
  return params;
}

export function registryStateToListParams(
  state: RiskAssessmentRegistryUrlState,
): RiskAssessmentListParams {
  const params: RiskAssessmentListParams = {
    offset: (state.page - 1) * state.pageSize,
    limit: state.pageSize,
    include_archived: state.includeArchived,
    include_superseded: state.includeSuperseded,
  };
  if (state.search) {
    params.search = state.search;
  }
  if (state.status) {
    params.status = state.status;
  }
  if (state.assessmentProfile) {
    params.assessment_profile = state.assessmentProfile;
  }
  if (state.hazardId) {
    params.hazard_id = state.hazardId;
  }
  if (state.assessedObjectType) {
    params.assessed_object_type = state.assessedObjectType;
  }
  if (state.createdFrom) {
    params.created_from = state.createdFrom;
  }
  if (state.createdTo) {
    params.created_to = state.createdTo;
  }
  return params;
}

export function hasActiveRiskAssessmentRegistryFilters(
  state: RiskAssessmentRegistryUrlState,
): boolean {
  return Boolean(
    state.search ||
    state.status ||
    state.assessmentProfile ||
    state.hazardId ||
    state.assessedObjectType ||
    state.includeArchived ||
    state.includeSuperseded !==
      DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE.includeSuperseded ||
    state.createdFrom ||
    state.createdTo,
  );
}
