import {
  COMPLIANCE_DOCUMENT_STATUSES,
  DOCUMENT_SUBJECT_KINDS,
  SAFETY_DOMAINS,
  type ComplianceDocumentListParams,
  type ComplianceDocumentStatus,
  type DocumentSubjectKind,
  type SafetyDomain,
} from "@/features/compliance-documents/types/compliance-documents-dto";

export interface ComplianceDocumentRegistryUrlState {
  search: string;
  status: ComplianceDocumentStatus | "";
  subjectKind: DocumentSubjectKind | "";
  safetyDomain: SafetyDomain | "";
  documentTypeIds: string[];
  reviewDueOnly: boolean;
  includeArchived: boolean;
  page: number;
  pageSize: number;
}

export const DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE: ComplianceDocumentRegistryUrlState =
  {
    search: "",
    status: "",
    subjectKind: "",
    safetyDomain: "",
    documentTypeIds: [],
    reviewDueOnly: false,
    includeArchived: false,
    page: 1,
    pageSize: 25,
  };

const PAGE_SIZE_MIN = 1;
const PAGE_SIZE_MAX = 200;

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

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function parseUuidList(values: string[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const raw of values) {
    const v = raw.trim().toLowerCase();
    if (UUID_RE.test(v) && !seen.has(v)) {
      seen.add(v);
      out.push(v);
    }
  }
  return out;
}

export function parseComplianceDocumentRegistrySearchParams(
  params: URLSearchParams,
): ComplianceDocumentRegistryUrlState {
  const pageSize = Math.min(
    PAGE_SIZE_MAX,
    Math.max(
      PAGE_SIZE_MIN,
      parsePositiveInt(
        params.get("pageSize"),
        DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE.pageSize,
      ),
    ),
  );
  return {
    search: params.get("search")?.trim() ?? "",
    status: parseEnum(params.get("status"), COMPLIANCE_DOCUMENT_STATUSES),
    subjectKind: parseEnum(params.get("subjectKind"), DOCUMENT_SUBJECT_KINDS),
    safetyDomain: parseEnum(params.get("safetyDomain"), SAFETY_DOMAINS),
    documentTypeIds: parseUuidList(params.getAll("documentTypeId")),
    reviewDueOnly: params.get("reviewDueOnly") === "true",
    includeArchived: params.get("includeArchived") === "true",
    page: parsePositiveInt(params.get("page"), 1),
    pageSize,
  };
}

export function serializeComplianceDocumentRegistrySearchParams(
  state: ComplianceDocumentRegistryUrlState,
): URLSearchParams {
  const params = new URLSearchParams();
  if (state.search) {
    params.set("search", state.search);
  }
  if (state.status) {
    params.set("status", state.status);
  }
  if (state.subjectKind) {
    params.set("subjectKind", state.subjectKind);
  }
  if (state.safetyDomain) {
    params.set("safetyDomain", state.safetyDomain);
  }
  for (const id of state.documentTypeIds) {
    params.append("documentTypeId", id);
  }
  if (state.reviewDueOnly) {
    params.set("reviewDueOnly", "true");
  }
  if (state.includeArchived) {
    params.set("includeArchived", "true");
  }
  if (state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.pageSize !== DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE.pageSize) {
    params.set("pageSize", String(state.pageSize));
  }
  return params;
}

export function registryStateToListParams(
  state: ComplianceDocumentRegistryUrlState,
): ComplianceDocumentListParams {
  const params: ComplianceDocumentListParams = {
    offset: (state.page - 1) * state.pageSize,
    limit: state.pageSize,
  };
  if (state.search) {
    params.search = state.search;
  }
  if (state.status) {
    params.status = state.status;
  }
  if (state.subjectKind) {
    params.subject_kind = state.subjectKind;
  }
  if (state.safetyDomain) {
    params.safety_domain = state.safetyDomain;
  }
  if (state.documentTypeIds.length > 0) {
    params.document_type_id = state.documentTypeIds;
  }
  if (state.reviewDueOnly) {
    params.review_due = true;
  }
  if (state.includeArchived) {
    params.include_archived = true;
  }
  return params;
}

export function hasActiveComplianceDocumentRegistryFilters(
  state: ComplianceDocumentRegistryUrlState,
): boolean {
  return Boolean(
    state.search ||
    state.status ||
    state.subjectKind ||
    state.safetyDomain ||
    state.documentTypeIds.length > 0 ||
    state.reviewDueOnly ||
    state.includeArchived,
  );
}
