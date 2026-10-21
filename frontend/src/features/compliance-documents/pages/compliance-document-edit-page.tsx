"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";

import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
  useToast,
} from "@/components";
import {
  PageActions,
  PageContainer,
  PageHeader,
} from "@/components/patterns/Page";

import { useUpdateComplianceDocumentMutation } from "@/features/compliance-documents/api/compliance-documents-mutations";
import {
  useComplianceDocumentDetailQuery,
  useDocumentTypesQuery,
} from "@/features/compliance-documents/api/compliance-documents-queries";
import { ComplianceDocumentForm } from "@/features/compliance-documents/components/compliance-document-form";
import { mapComplianceDocumentCapabilities } from "@/features/compliance-documents/hooks/use-compliance-document-permissions";
import {
  complianceDocumentToFormValues,
  formValuesToUpdateRequest,
} from "@/features/compliance-documents/mappers/compliance-document-form-mappers";
import {
  complianceDocumentFormSchema,
  defaultComplianceDocumentFormValues,
  type ComplianceDocumentFormValues,
} from "@/features/compliance-documents/schemas/compliance-document-form-schema";
import { useAuth } from "@/hooks/auth";
import {
  ConflictError,
  NotFoundError,
  PermissionError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

export function ComplianceDocumentEditPage({
  documentId,
}: {
  documentId: string;
}) {
  const { hasPermission } = useAuth();
  const capabilities = mapComplianceDocumentCapabilities(hasPermission);
  const router = useRouter();
  const { toast } = useToast();
  const detail = useComplianceDocumentDetailQuery(
    documentId,
    capabilities.canUpdate,
  );
  const typesQuery = useDocumentTypesQuery({ enabled: capabilities.canUpdate });
  const mutation = useUpdateComplianceDocumentMutation(documentId);
  const form = useForm<ComplianceDocumentFormValues>({
    resolver: zodResolver(complianceDocumentFormSchema),
    defaultValues: defaultComplianceDocumentFormValues,
    mode: "onSubmit",
  });

  useEffect(() => {
    window.document.title = "Редактировать документ · SafetyMAIN";
  }, []);

  // Hydrate the form once per documentId. Later refetches (window-focus, cache
  // invalidation) must not clobber in-progress user edits; the mutation sends
  // expected_version and the server surfaces real conflicts via 409.
  const hydratedForId = useRef<string | null>(null);
  useEffect(() => {
    if (detail.data && hydratedForId.current !== detail.data.id) {
      form.reset(complianceDocumentToFormValues(detail.data));
      hydratedForId.current = detail.data.id;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- hydrate only on first detail payload per id
  }, [detail.data?.id]);

  useEffect(() => {
    if (detail.data && detail.data.status !== "draft") {
      router.replace(`/compliance-documents/${documentId}`);
    }
  }, [detail.data, documentId, router]);

  if (!capabilities.canUpdate) {
    return (
      <PageContainer>
        <EmptyState
          title="Нельзя редактировать документ"
          description="Недостаточно прав для редактирования документов соответствия."
          action={
            <Button asChild variant="secondary">
              <Link href="/compliance-documents">К реестру</Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  if (detail.isLoading || typesQuery.isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Загрузка документа" />
      </PageContainer>
    );
  }

  if (detail.isError) {
    if (detail.error instanceof NotFoundError) {
      return (
        <PageContainer>
          <EmptyState
            title="Документ не найден"
            description="Документ не существует или недоступен в активной организации."
            action={
              <Button asChild variant="secondary">
                <Link href="/compliance-documents">К реестру</Link>
              </Button>
            }
          />
        </PageContainer>
      );
    }
    return (
      <PageContainer>
        <Alert tone="danger" title="Не удалось загрузить документ">
          {toUserSafeMessage(detail.error)}
        </Alert>
      </PageContainer>
    );
  }

  if (typesQuery.isError || !typesQuery.data) {
    return (
      <PageContainer>
        <Alert tone="danger" title="Не удалось загрузить типы документов">
          {toUserSafeMessage(typesQuery.error)}
        </Alert>
      </PageContainer>
    );
  }

  const document = detail.data;
  if (!document) {
    return null;
  }
  if (document.status !== "draft") {
    return (
      <PageContainer>
        <LoadingState label="Переход к документу" />
      </PageContainer>
    );
  }

  const currentVersion = document.version;

  async function onSubmit(values: ComplianceDocumentFormValues) {
    try {
      const updated = await mutation.mutateAsync(
        formValuesToUpdateRequest(values, currentVersion),
      );
      toast({
        tone: "success",
        title: "Документ сохранён",
        description: updated.code,
      });
      router.push(`/compliance-documents/${updated.id}`);
    } catch (error) {
      if (error instanceof ConflictError) {
        if (error.code === "duplicate_compliance_document_code") {
          form.setError("code", {
            message:
              error.message || "Документ с таким кодом уже существует в силе.",
          });
          form.setFocus("code");
          return;
        }
        // Version conflict or any other 409 — the field is not the issue.
        form.setError("root", {
          message: error.message || "Конфликт при сохранении документа.",
        });
        return;
      }
      if (error instanceof ValidationError) {
        form.setError("root", { message: error.message });
        return;
      }
      if (error instanceof PermissionError) {
        form.setError("root", { message: toUserSafeMessage(error) });
        return;
      }
      form.setError("root", { message: toUserSafeMessage(error) });
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title={`Редактировать · ${document.code}`}
        description="Изменения доступны только для черновиков."
        actions={
          <PageActions>
            <Button asChild variant="secondary">
              <Link href={`/compliance-documents/${document.id}`}>Отмена</Link>
            </Button>
            <Button
              type="submit"
              form="compliance-document-edit-form"
              loading={mutation.isPending}
              disabled={mutation.isPending}
            >
              Сохранить
            </Button>
          </PageActions>
        }
      />

      {form.formState.errors.root?.message ? (
        <Alert tone="danger" title="Не удалось сохранить документ">
          {form.formState.errors.root.message}
        </Alert>
      ) : null}

      <ComplianceDocumentForm
        id="compliance-document-edit-form"
        form={form}
        onSubmit={onSubmit}
        types={typesQuery.data.items}
        typeLocked
      />
    </PageContainer>
  );
}
