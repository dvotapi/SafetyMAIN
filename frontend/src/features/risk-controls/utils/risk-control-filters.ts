import type {
  ControlNatureDto,
  ControlTypeDto,
  EffectivenessResultDto,
  RiskControlListParams,
  RiskControlStatusDto,
} from "@/features/risk-controls/types/risk-control-dto";

export interface RiskControlRegistryUrlState {
  search: string;
  status: RiskControlStatusDto | "";
  hierarchyLevel: ControlTypeDto | "";
  controlNature: ControlNatureDto | "";
  effectiveness: EffectivenessResultDto | "";
  hazardId: string;
  riskAssessmentId: string;
  ownerReference: string;
  overdueOnly: boolean;
  awaitingVerification: boolean;
  includeTerminal: boolean;
  reviewDueBefore: string;
  reviewDueAfter: string;
  page: number;
  pageSize: number;
}

export const DEFAULT_RISK_CONTROL_REGISTRY_STATE: RiskControlRegistryUrlState =
  {
    search: "",
    status: "",
    hierarchyLevel: "",
    controlNature: "",
    effectiveness: "",
    hazardId: "",
    riskAssessmentId: "",
    ownerReference: "",
    overdueOnly: false,
    awaitingVerification: false,
    includeTerminal: false,
    reviewDueBefore: "",
    reviewDueAfter: "",
    page: 1,
    pageSize: 25,
  };

const STATUSES: readonly RiskControlStatusDto[] = [
  "draft",
  "planned",
  "in_implementation",
  "implemented",
  "verified_effective",
  "verified_ineffective",
  "suspended",
  "superseded",
  "archived",
  "cancelled",
];

const HIERARCHY_LEVELS: readonly ControlTypeDto[] = [
  "elimination",
  "substitution",
  "engineering",
  "administrative",
  "ppe",
];

const CONTROL_NATURES: readonly ControlNatureDto[] = [
  "preventive",
  "detective",
  "mitigating",
  "recovery",
];

const EFFECTIVENESS_RESULTS: readonly EffectivenessResultDto[] = [
  "effective",
  "partially_effective",
  "ineffective",
  "not_verified",
  "not_applicable",
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

function dateOnlyToApiDatetime(dateOnly: string): string {
  return `${dateOnly}T00:00:00Z`;
}

export function parseRiskControlRegistrySearchParams(
  params: URLSearchParams,
): RiskControlRegistryUrlState {
  const pageSize = Math.min(
    200,
    Math.max(
      1,
      parsePositiveInt(
        params.get("pageSize"),
        DEFAULT_RISK_CONTROL_REGISTRY_STATE.pageSize,
      ),
    ),
  );
  return {
    search: params.get("search")?.trim() ?? "",
    status: parseEnum(params.get("status"), STATUSES),
    hierarchyLevel: parseEnum(params.get("hierarchyLevel"), HIERARCHY_LEVELS),
    controlNature: parseEnum(params.get("controlNature"), CONTROL_NATURES),
    effectiveness: parseEnum(
      params.get("effectiveness"),
      EFFECTIVENESS_RESULTS,
    ),
    hazardId: params.get("hazardId")?.trim() ?? "",
    riskAssessmentId: params.get("riskAssessmentId")?.trim() ?? "",
    ownerReference: params.get("ownerReference")?.trim() ?? "",
    overdueOnly: params.get("overdueOnly") === "true",
    awaitingVerification: params.get("awaitingVerification") === "true",
    includeTerminal: params.get("includeTerminal") === "true",
    reviewDueBefore: params.get("reviewDueBefore")?.trim() ?? "",
    reviewDueAfter: params.get("reviewDueAfter")?.trim() ?? "",
    page: parsePositiveInt(params.get("page"), 1),
    pageSize,
  };
}

export function serializeRiskControlRegistrySearchParams(
  state: RiskControlRegistryUrlState,
): URLSearchParams {
  const params = new URLSearchParams();
  if (state.search) {
    params.set("search", state.search);
  }
  if (state.status) {
    params.set("status", state.status);
  }
  if (state.hierarchyLevel) {
    params.set("hierarchyLevel", state.hierarchyLevel);
  }
  if (state.controlNature) {
    params.set("controlNature", state.controlNature);
  }
  if (state.effectiveness) {
    params.set("effectiveness", state.effectiveness);
  }
  if (state.hazardId) {
    params.set("hazardId", state.hazardId);
  }
  if (state.riskAssessmentId) {
    params.set("riskAssessmentId", state.riskAssessmentId);
  }
  if (state.ownerReference) {
    params.set("ownerReference", state.ownerReference);
  }
  if (state.overdueOnly) {
    params.set("overdueOnly", "true");
  }
  if (state.awaitingVerification) {
    params.set("awaitingVerification", "true");
  }
  if (state.includeTerminal) {
    params.set("includeTerminal", "true");
  }
  if (state.reviewDueBefore) {
    params.set("reviewDueBefore", state.reviewDueBefore);
  }
  if (state.reviewDueAfter) {
    params.set("reviewDueAfter", state.reviewDueAfter);
  }
  if (state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.pageSize !== DEFAULT_RISK_CONTROL_REGISTRY_STATE.pageSize) {
    params.set("pageSize", String(state.pageSize));
  }
  return params;
}

export function registryStateToListParams(
  state: RiskControlRegistryUrlState,
): RiskControlListParams {
  const params: RiskControlListParams = {
    offset: (state.page - 1) * state.pageSize,
    limit: state.pageSize,
  };
  if (state.search) {
    params.search = state.search;
  }
  if (state.status) {
    params.status = state.status;
  }
  if (state.hierarchyLevel) {
    params.hierarchy_level = state.hierarchyLevel;
  }
  if (state.controlNature) {
    params.control_nature = state.controlNature;
  }
  if (state.effectiveness) {
    params.latest_effectiveness_result = state.effectiveness;
  }
  if (state.hazardId) {
    params.hazard_id = state.hazardId;
  }
  if (state.riskAssessmentId) {
    params.risk_assessment_id = state.riskAssessmentId;
  }
  if (state.ownerReference) {
    params.owner_reference = state.ownerReference;
  }
  if (state.overdueOnly) {
    params.overdue_only = state.overdueOnly;
  }
  if (state.awaitingVerification) {
    params.awaiting_verification = state.awaitingVerification;
  }
  if (state.includeTerminal) {
    params.include_terminal = state.includeTerminal;
  }
  if (state.reviewDueBefore) {
    params.review_due_before = dateOnlyToApiDatetime(state.reviewDueBefore);
  }
  if (state.reviewDueAfter) {
    params.review_due_after = dateOnlyToApiDatetime(state.reviewDueAfter);
  }
  return params;
}

export function hasActiveRiskControlRegistryFilters(
  state: RiskControlRegistryUrlState,
): boolean {
  return Boolean(
    state.search ||
    state.status ||
    state.hierarchyLevel ||
    state.controlNature ||
    state.effectiveness ||
    state.hazardId ||
    state.riskAssessmentId ||
    state.ownerReference ||
    state.overdueOnly ||
    state.awaitingVerification ||
    state.includeTerminal ||
    state.reviewDueBefore ||
    state.reviewDueAfter,
  );
}
