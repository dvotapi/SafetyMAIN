"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  bulkExcludeShelfSlots,
  confirmShelfSlotApplicable,
  developShelfSlot,
  excludeShelfSlot,
  getShelfSlot,
  linkShelfSlotDocument,
  restoreShelfSlot,
} from "@/features/document-shelf/api/shelf-api";
import { shelfKeys } from "@/features/document-shelf/api/shelf-query-keys";
import type {
  ShelfSlotDetailDto,
  SlotExclusionReason,
} from "@/features/document-shelf/types/shelf-dto";
import { useOrganization } from "@/hooks/auth";

/** Every shelf command refreshes the overview, the opened shelf and the panel. */
function useShelfMutation<TInput, TResult>(
  fn: (input: TInput) => Promise<TResult>,
) {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return useMutation({
    mutationFn: fn,
    onSuccess: (result) => {
      if (
        result &&
        typeof result === "object" &&
        "code" in result &&
        "id" in result
      ) {
        const detail = result as unknown as ShelfSlotDetailDto;
        queryClient.setQueryData(
          shelfKeys.slot(organizationId, detail.id),
          detail,
        );
      }
      void queryClient.invalidateQueries({
        queryKey: shelfKeys.all(organizationId),
      });
    },
  });
}

export function useExcludeShelfSlotMutation() {
  return useShelfMutation(
    (input: {
      slotId: string;
      reason: SlotExclusionReason;
      comment: string;
      version: number;
    }) =>
      excludeShelfSlot(input.slotId, {
        reason: input.reason,
        comment: input.comment,
        version: input.version,
      }),
  );
}

/**
 * Bulk exclusion needs each place's current version, which the summaries do
 * not carry; it is read from the place detail just before the request.
 */
export function useBulkExcludeShelfSlotsMutation() {
  return useShelfMutation(
    async (input: {
      slotIds: string[];
      reason: SlotExclusionReason;
      comment: string;
    }) => {
      const details = await Promise.all(
        input.slotIds.map((id) => getShelfSlot(id)),
      );
      return bulkExcludeShelfSlots({
        items: details.map((detail) => ({
          slot_id: detail.id,
          version: detail.version,
        })),
        reason: input.reason,
        comment: input.comment,
      });
    },
  );
}

/** Undo after exclusion: restore each place at its current version. */
export function useRestoreShelfSlotsMutation() {
  return useShelfMutation(async (slotIds: string[]) => {
    const details = await Promise.all(slotIds.map((id) => getShelfSlot(id)));
    return Promise.all(
      details.map((detail) => restoreShelfSlot(detail.id, detail.version)),
    );
  });
}

export function useRestoreShelfSlotMutation() {
  return useShelfMutation((input: { slotId: string; version: number }) =>
    restoreShelfSlot(input.slotId, input.version),
  );
}

export function useConfirmShelfSlotApplicableMutation() {
  return useShelfMutation((input: { slotId: string; version: number }) =>
    confirmShelfSlotApplicable(input.slotId, input.version),
  );
}

export function useLinkShelfSlotDocumentMutation() {
  return useShelfMutation(
    (input: { slotId: string; documentId: string; version: number }) =>
      linkShelfSlotDocument(input.slotId, input.documentId, input.version),
  );
}

export function useDevelopShelfSlotMutation() {
  return useShelfMutation(
    (input: { slotId: string; version: number; documentTypeCode?: string }) =>
      developShelfSlot(input.slotId, {
        version: input.version,
        ...(input.documentTypeCode
          ? { document_type_code: input.documentTypeCode }
          : {}),
      }),
  );
}
