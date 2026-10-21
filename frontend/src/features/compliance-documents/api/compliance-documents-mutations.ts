"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  confirmComplianceDocumentFile,
  createComplianceDocument,
  createComplianceDocumentUploadUrl,
  updateComplianceDocument,
} from "@/features/compliance-documents/api/compliance-documents-api";
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
  ComplianceDocumentUploadUrlRequest,
  CompleteReviewRequestDto,
  ConfirmComplianceDocumentFileRequest,
  CreateComplianceDocumentRequest,
  ReasonRequestDto,
  UpdateComplianceDocumentRequest,
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

export function useCreateComplianceDocumentMutation() {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return useMutation({
    mutationFn: (body: CreateComplianceDocumentRequest) =>
      createComplianceDocument(body),
    onSuccess: (document) => {
      queryClient.setQueryData(
        complianceDocumentKeys.detail(organizationId, document.id),
        document,
      );
      void queryClient.invalidateQueries({
        queryKey: complianceDocumentKeys.lists(organizationId),
      });
    },
  });
}

export function useUpdateComplianceDocumentMutation(documentId: string) {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return useMutation({
    mutationFn: (body: UpdateComplianceDocumentRequest) =>
      updateComplianceDocument(documentId, body),
    onSuccess: (document) => {
      queryClient.setQueryData(
        complianceDocumentKeys.detail(organizationId, document.id),
        document,
      );
      void queryClient.invalidateQueries({
        queryKey: complianceDocumentKeys.lists(organizationId),
      });
    },
  });
}

export function useCreateComplianceDocumentUploadUrlMutation(
  documentId: string,
) {
  return useMutation({
    mutationFn: (body: ComplianceDocumentUploadUrlRequest) =>
      createComplianceDocumentUploadUrl(documentId, body),
  });
}

export function useConfirmComplianceDocumentFileMutation(documentId: string) {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return useMutation({
    mutationFn: (body: ConfirmComplianceDocumentFileRequest) =>
      confirmComplianceDocumentFile(documentId, body),
    onSuccess: (document) => {
      queryClient.setQueryData(
        complianceDocumentKeys.detail(organizationId, document.id),
        document,
      );
      void queryClient.invalidateQueries({
        queryKey: complianceDocumentKeys.fileVersions(
          organizationId,
          document.id,
        ),
      });
      void queryClient.invalidateQueries({
        queryKey: complianceDocumentKeys.lists(organizationId),
      });
    },
  });
}

export function useRestoreComplianceDocumentMutation(documentId: string) {
  return useLifecycleMutation<ReasonRequestDto>(
    documentId,
    restoreComplianceDocument,
  );
}
