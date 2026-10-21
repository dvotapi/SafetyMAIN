import { apiClient } from "@/services/api/client";

import {
  complianceDocumentDownloadUrlSchema,
  complianceDocumentFilesListSchema,
  complianceDocumentListSchema,
  complianceDocumentSchema,
} from "@/features/compliance-documents/schemas/compliance-documents-response-schemas";
import type {
  ComplianceDocumentDto,
  ComplianceDocumentDownloadUrlDto,
  ComplianceDocumentFilesListDto,
  ComplianceDocumentListDto,
  ComplianceDocumentListParams,
} from "@/features/compliance-documents/types/compliance-documents-dto";

const BASE_PATH = "/api/v1/compliance-documents";

function requireBody<T>(value: T | null, label: string): T {
  if (value === null || value === undefined) {
    throw new Error(`Empty ${label} response`);
  }
  return value;
}

function toQuery(
  params: ComplianceDocumentListParams,
): Record<string, string | number | boolean | undefined> {
  const query: Record<string, string | number | boolean | undefined> = {
    offset: params.offset ?? 0,
    limit: params.limit ?? 25,
  };
  if (params.status) query.status = params.status;
  if (params.subject_kind) query.subject_kind = params.subject_kind;
  if (params.safety_domain) query.safety_domain = params.safety_domain;
  if (params.review_due !== undefined) query.review_due = params.review_due;
  if (params.include_archived) query.include_archived = true;
  if (params.search) query.search = params.search;
  return query;
}

export async function listComplianceDocuments(
  params: ComplianceDocumentListParams,
  signal?: AbortSignal,
): Promise<ComplianceDocumentListDto> {
  // `document_type_id` is a repeatable query param; append each UUID as its
  // own entry so the backend reads it as a list.
  const typeIds = params.document_type_id ?? [];
  const search = new URLSearchParams();
  const base = toQuery(params);
  for (const [key, value] of Object.entries(base)) {
    if (value === undefined || value === null) continue;
    search.set(key, String(value));
  }
  for (const id of typeIds) {
    search.append("document_type_id", id);
  }
  const qs = search.toString();
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: qs ? `${BASE_PATH}?${qs}` : BASE_PATH,
    ...(signal ? { signal } : {}),
  });
  return complianceDocumentListSchema.parse(
    requireBody(dto, "compliance document list"),
  );
}

export async function getComplianceDocument(
  documentId: string,
  signal?: AbortSignal,
): Promise<ComplianceDocumentDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/${documentId}`,
    ...(signal ? { signal } : {}),
  });
  return complianceDocumentSchema.parse(
    requireBody(dto, "compliance document"),
  );
}

export async function getComplianceDocumentDownloadUrl(
  documentId: string,
  signal?: AbortSignal,
): Promise<ComplianceDocumentDownloadUrlDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/${documentId}/files/current/download-url`,
    ...(signal ? { signal } : {}),
  });
  return complianceDocumentDownloadUrlSchema.parse(
    requireBody(dto, "compliance document download url"),
  );
}

export async function listComplianceDocumentFileVersions(
  documentId: string,
  signal?: AbortSignal,
): Promise<ComplianceDocumentFilesListDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/${documentId}/files/versions`,
    ...(signal ? { signal } : {}),
  });
  return complianceDocumentFilesListSchema.parse(
    requireBody(dto, "compliance document file versions"),
  );
}
