"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getShelfOverview,
  getShelfSectionSlots,
  getShelfSlot,
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
