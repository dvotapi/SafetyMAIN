import { apiClient } from "@/services/api/client";

import { documentTypeListSchema } from "@/features/compliance-documents/schemas/compliance-documents-response-schemas";
import type { DocumentTypeListDto } from "@/features/compliance-documents/types/compliance-documents-dto";

export async function listDocumentTypes(
  options: { includeInactive?: boolean } = {},
  signal?: AbortSignal,
): Promise<DocumentTypeListDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: "/api/v1/document-types",
    ...(options.includeInactive ? { query: { include_inactive: true } } : {}),
    ...(signal ? { signal } : {}),
  });
  if (!dto) {
    throw new Error("Empty document types response");
  }
  return documentTypeListSchema.parse(dto);
}
