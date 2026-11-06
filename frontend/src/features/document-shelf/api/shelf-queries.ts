"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getFileViewUrl,
  getShelfDocument,
  getShelfOverview,
  getShelfSectionSlots,
  getShelfSlot,
  listActiveDocumentTypes,
  searchOrganizationDocuments,
  searchShelfSlots,
} from "@/features/document-shelf/api/shelf-api";
import { shelfKeys } from "@/features/document-shelf/api/shelf-query-keys";
import { useOrganization } from "@/hooks/auth";

export function useShelfOverviewQuery(enabled = true) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: shelfKeys.overview(organizationId),
    queryFn: ({ signal }) => getShelfOverview(signal),
    enabled: enabled && Boolean(organizationId),
  });
}

export function useShelfSectionSlotsQuery(sectionCode: string | null) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: shelfKeys.section(organizationId, sectionCode ?? ""),
    queryFn: ({ signal }) => getShelfSectionSlots(sectionCode ?? "", signal),
    enabled: Boolean(organizationId) && Boolean(sectionCode),
  });
}

export function useShelfSlotQuery(slotId: string | null) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: shelfKeys.slot(organizationId, slotId ?? ""),
    queryFn: ({ signal }) => getShelfSlot(slotId ?? "", signal),
    enabled: Boolean(organizationId) && Boolean(slotId),
  });
}

export function useShelfSearchQuery(query: string) {
  const { organizationId } = useOrganization();
  const trimmed = query.trim();
  return useQuery({
    queryKey: shelfKeys.search(organizationId, trimmed),
    queryFn: ({ signal }) => searchShelfSlots(trimmed, 20, signal),
    enabled: Boolean(organizationId) && trimmed.length >= 2,
    staleTime: 30_000,
  });
}

export function useShelfFileViewUrlQuery(
  documentId: string | null,
  fileId: string | null,
) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: shelfKeys.fileViewUrl(
      organizationId,
      documentId ?? "",
      fileId ?? "",
    ),
    queryFn: ({ signal }) =>
      getFileViewUrl(documentId ?? "", fileId ?? "", signal),
    enabled: Boolean(organizationId && documentId && fileId),
    // Reuse the URL until shortly before it expires; never refetch on focus.
    staleTime: (query) => {
      const expiresAt = query.state.data?.expires_at;
      if (!expiresAt) return 5 * 60_000;
      return Math.max(0, Date.parse(expiresAt) - Date.now() - 60_000);
    },
    refetchOnWindowFocus: false,
  });
}

export function useShelfDocumentQuery(documentId: string | null) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: [...shelfKeys.all(organizationId), "document", documentId],
    queryFn: ({ signal }) => getShelfDocument(documentId ?? "", signal),
    enabled: Boolean(organizationId && documentId),
  });
}

export function useDocumentSearchQuery(search: string) {
  const { organizationId } = useOrganization();
  const trimmed = search.trim();
  return useQuery({
    queryKey: [...shelfKeys.all(organizationId), "documents", trimmed],
    queryFn: ({ signal }) => searchOrganizationDocuments(trimmed, signal),
    enabled: Boolean(organizationId) && trimmed.length >= 2,
  });
}

export function useActiveDocumentTypesQuery(enabled: boolean) {
  const { organizationId } = useOrganization();
  return useQuery({
    queryKey: [...shelfKeys.all(organizationId), "document-types"],
    queryFn: ({ signal }) => listActiveDocumentTypes(signal),
    enabled: enabled && Boolean(organizationId),
    staleTime: 300_000,
  });
}
