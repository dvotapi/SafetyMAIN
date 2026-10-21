import { apiClient } from "@/services/api/client";

import { assertComplianceDocumentId } from "@/features/compliance-documents/api/compliance-documents-id";
import {
  complianceDocumentDownloadUrlSchema,
  complianceDocumentFilesListSchema,
  complianceDocumentListSchema,
  complianceDocumentSchema,
  complianceDocumentUploadUrlSchema,
} from "@/features/compliance-documents/schemas/compliance-documents-response-schemas";
import type {
  ComplianceDocumentDto,
  ComplianceDocumentDownloadUrlDto,
  ComplianceDocumentFilesListDto,
  ComplianceDocumentListDto,
  ComplianceDocumentListParams,
  ComplianceDocumentUploadUrlDto,
  ComplianceDocumentUploadUrlRequest,
  ConfirmComplianceDocumentFileRequest,
  CreateComplianceDocumentRequest,
  UpdateComplianceDocumentRequest,
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
  const id = assertComplianceDocumentId(documentId);
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/${id}`,
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
  const id = assertComplianceDocumentId(documentId);
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/${id}/files/current/download-url`,
    ...(signal ? { signal } : {}),
  });
  return complianceDocumentDownloadUrlSchema.parse(
    requireBody(dto, "compliance document download url"),
  );
}

export async function createComplianceDocument(
  body: CreateComplianceDocumentRequest,
): Promise<ComplianceDocumentDto> {
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path: BASE_PATH,
    body,
  });
  return complianceDocumentSchema.parse(
    requireBody(dto, "create compliance document"),
  );
}

export async function updateComplianceDocument(
  documentId: string,
  body: UpdateComplianceDocumentRequest,
): Promise<ComplianceDocumentDto> {
  const id = assertComplianceDocumentId(documentId);
  const dto = await apiClient.request<unknown>({
    method: "PATCH",
    path: `${BASE_PATH}/${id}`,
    body,
  });
  return complianceDocumentSchema.parse(
    requireBody(dto, "update compliance document"),
  );
}

export async function createComplianceDocumentUploadUrl(
  documentId: string,
  body: ComplianceDocumentUploadUrlRequest,
): Promise<ComplianceDocumentUploadUrlDto> {
  const id = assertComplianceDocumentId(documentId);
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path: `${BASE_PATH}/${id}/files/upload-url`,
    body,
  });
  return complianceDocumentUploadUrlSchema.parse(
    requireBody(dto, "compliance document upload url"),
  );
}

export async function confirmComplianceDocumentFile(
  documentId: string,
  body: ConfirmComplianceDocumentFileRequest,
): Promise<ComplianceDocumentDto> {
  const id = assertComplianceDocumentId(documentId);
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path: `${BASE_PATH}/${id}/files/confirm`,
    body,
  });
  return complianceDocumentSchema.parse(
    requireBody(dto, "confirm compliance document file"),
  );
}

export async function listComplianceDocumentFileVersions(
  documentId: string,
  signal?: AbortSignal,
): Promise<ComplianceDocumentFilesListDto> {
  const id = assertComplianceDocumentId(documentId);
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/${id}/files/versions`,
    ...(signal ? { signal } : {}),
  });
  return complianceDocumentFilesListSchema.parse(
    requireBody(dto, "compliance document file versions"),
  );
}
