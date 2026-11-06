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

/** Upper bound of one bulk request (docs/api/ShelfAPI.md). */
export const BULK_EXCLUDE_MAX_ITEMS = 200;

/**
 * Sends the versions the user saw on the shelf, so a place changed in the
 * meantime is a 409 conflict rather than silently excluded.
 */
export function useBulkExcludeShelfSlotsMutation() {
  return useShelfMutation(
    (input: {
      items: Array<{ slot_id: string; version: number }>;
      reason: SlotExclusionReason;
      comment: string;
    }) => bulkExcludeShelfSlots(input),
  );
}

/**
 * Undo after exclusion: restore each place at its current version. Places are
 * restored independently; the result names the ones that failed, so a retry
 * touches only those.
 */
export function useRestoreShelfSlotsMutation() {
  return useShelfMutation(async (slotIds: string[]) => {
    const results = await Promise.allSettled(
      slotIds.map(async (id) => {
        const detail = await getShelfSlot(id);
        return restoreShelfSlot(detail.id, detail.version);
      }),
    );
    const failed = slotIds.filter(
      (_, index) => results[index]?.status === "rejected",
    );
    const firstError = results.find(
      (result): result is PromiseRejectedResult => result.status === "rejected",
    )?.reason as unknown;
    return { failed, firstError };
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

/** After a file upload elsewhere (the reused compliance dialog), refresh the whole shelf. */
export function useRefreshShelf() {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return () =>
    queryClient.invalidateQueries({ queryKey: shelfKeys.all(organizationId) });
}
