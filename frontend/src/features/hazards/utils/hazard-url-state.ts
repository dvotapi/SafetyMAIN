import type {
  HazardCategoryDto,
  HazardListParams,
  HazardSourceDto,
  HazardStatusDto,
  SafetyDirectionDto,
} from "@/features/hazards/types/hazard-types";
import {
  HAZARD_CATEGORIES,
  HAZARD_SOURCES,
  SAFETY_DIRECTIONS,
} from "@/features/hazards/schemas/hazard-form-schema";

export interface HazardRegistryUrlState {
  search: string;
  status: HazardStatusDto | "";
  category: HazardCategoryDto | "";
  source: HazardSourceDto | "";
  safetyDirection: SafetyDirectionDto | "";
  includeArchived: boolean;
  page: number;
  pageSize: number;
}

export const DEFAULT_REGISTRY_STATE: HazardRegistryUrlState = {
  search: "",
  status: "",
  category: "",
  source: "",
  safetyDirection: "",
  includeArchived: false,
  page: 1,
  pageSize: 25,
};

const STATUSES: readonly HazardStatusDto[] = ["draft", "active", "archived"];

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

export function parseRegistrySearchParams(
  params: URLSearchParams,
): HazardRegistryUrlState {
  const pageSize = Math.min(
    200,
    Math.max(
      1,
      parsePositiveInt(params.get("pageSize"), DEFAULT_REGISTRY_STATE.pageSize),
    ),
  );
  return {
    search: params.get("search")?.trim() ?? "",
    status: parseEnum(params.get("status"), STATUSES),
    category: parseEnum(params.get("category"), HAZARD_CATEGORIES),
    source: parseEnum(params.get("source"), HAZARD_SOURCES),
    safetyDirection: parseEnum(
      params.get("safetyDirection"),
      SAFETY_DIRECTIONS,
    ),
    includeArchived: params.get("includeArchived") === "true",
    page: parsePositiveInt(params.get("page"), 1),
    pageSize,
  };
}

export function serializeRegistrySearchParams(
  state: HazardRegistryUrlState,
): URLSearchParams {
  const params = new URLSearchParams();
  if (state.search) {
    params.set("search", state.search);
  }
  if (state.status) {
    params.set("status", state.status);
  }
  if (state.category) {
    params.set("category", state.category);
  }
  if (state.source) {
    params.set("source", state.source);
  }
  if (state.safetyDirection) {
    params.set("safetyDirection", state.safetyDirection);
  }
  if (state.includeArchived) {
    params.set("includeArchived", "true");
  }
  if (state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.pageSize !== DEFAULT_REGISTRY_STATE.pageSize) {
    params.set("pageSize", String(state.pageSize));
  }
  return params;
}

export function registryStateToListParams(
  state: HazardRegistryUrlState,
): HazardListParams {
  const params: HazardListParams = {
    offset: (state.page - 1) * state.pageSize,
    limit: state.pageSize,
    include_archived: state.includeArchived,
  };
  if (state.search) {
    params.search = state.search;
  }
  if (state.status) {
    params.status = state.status;
  }
  if (state.category) {
    params.category = state.category;
  }
  if (state.source) {
    params.source = state.source;
  }
  if (state.safetyDirection) {
    params.safety_direction = state.safetyDirection;
  }
  return params;
}

export function hasActiveRegistryFilters(
  state: HazardRegistryUrlState,
): boolean {
  return Boolean(
    state.search ||
    state.status ||
    state.category ||
    state.source ||
    state.safetyDirection ||
    state.includeArchived,
  );
}
