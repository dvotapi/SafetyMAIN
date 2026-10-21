import { apiClient } from "@/services/api/client";

import { complianceDocumentSchema } from "@/features/compliance-documents/schemas/compliance-documents-response-schemas";
import type {
  ComplianceDocumentDto,
  CompleteReviewRequestDto,
  ReasonRequestDto,
  VersionedRequestDto,
} from "@/features/compliance-documents/types/compliance-documents-dto";

const BASE_PATH = "/api/v1/compliance-documents";

async function postLifecycle(
  path: string,
  body: object,
): Promise<ComplianceDocumentDto> {
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path,
    body,
  });
  if (!dto) {
    throw new Error(`Empty response from ${path}`);
  }
  return complianceDocumentSchema.parse(dto);
}

export function approveComplianceDocument(
  documentId: string,
  body: VersionedRequestDto,
): Promise<ComplianceDocumentDto> {
  return postLifecycle(`${BASE_PATH}/${documentId}/approve`, body);
}

export function activateComplianceDocument(
  documentId: string,
  body: VersionedRequestDto,
): Promise<ComplianceDocumentDto> {
  return postLifecycle(`${BASE_PATH}/${documentId}/activate`, body);
}

export function startReviewComplianceDocument(
  documentId: string,
  body: VersionedRequestDto,
): Promise<ComplianceDocumentDto> {
  return postLifecycle(`${BASE_PATH}/${documentId}/start-review`, body);
}

export function completeReviewComplianceDocument(
  documentId: string,
  body: CompleteReviewRequestDto,
): Promise<ComplianceDocumentDto> {
  return postLifecycle(`${BASE_PATH}/${documentId}/complete-review`, body);
}

export function archiveComplianceDocument(
  documentId: string,
  body: ReasonRequestDto,
): Promise<ComplianceDocumentDto> {
  return postLifecycle(`${BASE_PATH}/${documentId}/archive`, body);
}

export function restoreComplianceDocument(
  documentId: string,
  body: ReasonRequestDto,
): Promise<ComplianceDocumentDto> {
  return postLifecycle(`${BASE_PATH}/${documentId}/restore`, body);
}
