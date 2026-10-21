"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  activateComplianceDocument,
  approveComplianceDocument,
  archiveComplianceDocument,
  completeReviewComplianceDocument,
  restoreComplianceDocument,
  startReviewComplianceDocument,
} from "@/features/compliance-documents/api/compliance-documents-commands";
import { complianceDocumentKeys } from "@/features/compliance-documents/api/compliance-documents-query-keys";
import type {
  ComplianceDocumentDto,
  CompleteReviewRequestDto,
  ReasonRequestDto,
  VersionedRequestDto,
} from "@/features/compliance-documents/types/compliance-documents-dto";
import { useOrganization } from "@/hooks/auth";

function useLifecycleMutation<TDto>(
  documentId: string,
  commandFn: (id: string, body: TDto) => Promise<ComplianceDocumentDto>,
  options: { refreshSupersededEdition?: boolean } = {},
) {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return useMutation({
    mutationFn: (body: TDto) => commandFn(documentId, body),
    onSuccess: (document) => {
      queryClient.setQueryData(
        complianceDocumentKeys.detail(organizationId, document.id),
        document,
      );
      void queryClient.invalidateQueries({
        queryKey: complianceDocumentKeys.lists(organizationId),
      });
      // Only activation atomically supersedes a previous edition; other
      // lifecycle actions never touch another document, so skip the extra
      // refetch there.
      if (options.refreshSupersededEdition && document.supersedes_document_id) {
        void queryClient.invalidateQueries({
          queryKey: complianceDocumentKeys.detail(
            organizationId,
            document.supersedes_document_id,
          ),
        });
      }
    },
  });
}

export function useApproveComplianceDocumentMutation(documentId: string) {
  return useLifecycleMutation<VersionedRequestDto>(
    documentId,
    approveComplianceDocument,
  );
}

export function useActivateComplianceDocumentMutation(documentId: string) {
  return useLifecycleMutation<VersionedRequestDto>(
    documentId,
    activateComplianceDocument,
    { refreshSupersededEdition: true },
  );
}

export function useStartReviewComplianceDocumentMutation(documentId: string) {
  return useLifecycleMutation<VersionedRequestDto>(
    documentId,
    startReviewComplianceDocument,
  );
}

export function useCompleteReviewComplianceDocumentMutation(
  documentId: string,
) {
  return useLifecycleMutation<CompleteReviewRequestDto>(
    documentId,
    completeReviewComplianceDocument,
  );
}

export function useArchiveComplianceDocumentMutation(documentId: string) {
  return useLifecycleMutation<ReasonRequestDto>(
    documentId,
    archiveComplianceDocument,
  );
}

export function useRestoreComplianceDocumentMutation(documentId: string) {
  return useLifecycleMutation<ReasonRequestDto>(
    documentId,
    restoreComplianceDocument,
  );
}
