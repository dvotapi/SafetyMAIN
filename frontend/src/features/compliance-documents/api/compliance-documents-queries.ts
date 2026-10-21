"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getComplianceDocument,
  listComplianceDocumentFileVersions,
  listComplianceDocuments,
} from "@/features/compliance-documents/api/compliance-documents-api";
import {
  complianceDocumentKeys,
  documentTypeKeys,
} from "@/features/compliance-documents/api/compliance-documents-query-keys";
import { listDocumentTypes } from "@/features/compliance-documents/api/document-types-api";
import type { ComplianceDocumentListParams } from "@/features/compliance-documents/types/compliance-documents-dto";
import { useOrganization } from "@/hooks/auth";

export function useComplianceDocumentListQuery(
  filters: ComplianceDocumentListParams,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: complianceDocumentKeys.list(organizationId, filters),
    queryFn: ({ signal }) => listComplianceDocuments(filters, signal),
    enabled: enabled && Boolean(organizationId),
  });
}

export function useComplianceDocumentDetailQuery(
  documentId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: complianceDocumentKeys.detail(organizationId, documentId),
    queryFn: ({ signal }) => getComplianceDocument(documentId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(documentId),
  });
}

export function useComplianceDocumentFileVersionsQuery(
  documentId: string,
  enabled = true,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: complianceDocumentKeys.fileVersions(organizationId, documentId),
    queryFn: ({ signal }) =>
      listComplianceDocumentFileVersions(documentId, signal),
    enabled: enabled && Boolean(organizationId) && Boolean(documentId),
  });
}

export function useDocumentTypesQuery(
  options: { includeInactive?: boolean; enabled?: boolean } = {},
) {
  const { organizationId } = useOrganization();
  const includeInactive = options.includeInactive ?? false;
  const enabled = options.enabled ?? true;
  return useQuery({
    queryKey: documentTypeKeys.list(organizationId, includeInactive),
    queryFn: ({ signal }) => listDocumentTypes({ includeInactive }, signal),
    enabled: enabled && Boolean(organizationId),
  });
}
