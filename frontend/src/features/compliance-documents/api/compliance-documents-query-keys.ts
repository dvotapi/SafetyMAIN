import type { ComplianceDocumentListParams } from "@/features/compliance-documents/types/compliance-documents-dto";

export const complianceDocumentKeys = {
  all: (organizationId: string | null) =>
    ["compliance-documents", organizationId ?? "none"] as const,
  lists: (organizationId: string | null) =>
    [...complianceDocumentKeys.all(organizationId), "list"] as const,
  list: (
    organizationId: string | null,
    filters: ComplianceDocumentListParams,
  ) => [...complianceDocumentKeys.lists(organizationId), filters] as const,
  details: (organizationId: string | null) =>
    [...complianceDocumentKeys.all(organizationId), "detail"] as const,
  detail: (organizationId: string | null, documentId: string) =>
    [...complianceDocumentKeys.details(organizationId), documentId] as const,
  fileVersions: (organizationId: string | null, documentId: string) =>
    [
      ...complianceDocumentKeys.detail(organizationId, documentId),
      "file-versions",
    ] as const,
};

export const documentTypeKeys = {
  all: (organizationId: string | null) =>
    ["document-types", organizationId ?? "none"] as const,
  list: (organizationId: string | null, includeInactive: boolean) =>
    [...documentTypeKeys.all(organizationId), "list", includeInactive] as const,
};
