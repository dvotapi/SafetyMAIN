"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
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

import { useCreateComplianceDocumentMutation } from "@/features/compliance-documents/api/compliance-documents-mutations";
import { useDocumentTypesQuery } from "@/features/compliance-documents/api/compliance-documents-queries";
import { ComplianceDocumentForm } from "@/features/compliance-documents/components/compliance-document-form";
import { mapComplianceDocumentCapabilities } from "@/features/compliance-documents/hooks/use-compliance-document-permissions";
import { formValuesToCreateRequest } from "@/features/compliance-documents/mappers/compliance-document-form-mappers";
import {
  complianceDocumentFormSchema,
  defaultComplianceDocumentFormValues,
  type ComplianceDocumentFormValues,
} from "@/features/compliance-documents/schemas/compliance-document-form-schema";
import { useAuth } from "@/hooks/auth";
import {
  ConflictError,
  PermissionError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

export function ComplianceDocumentCreatePage() {
  const { hasPermission } = useAuth();
  const capabilities = mapComplianceDocumentCapabilities(hasPermission);
  const router = useRouter();
  const { toast } = useToast();
  const typesQuery = useDocumentTypesQuery({ enabled: capabilities.canCreate });
  const mutation = useCreateComplianceDocumentMutation();
  const form = useForm<ComplianceDocumentFormValues>({
    resolver: zodResolver(complianceDocumentFormSchema),
    defaultValues: defaultComplianceDocumentFormValues,
    mode: "onSubmit",
  });

  useEffect(() => {
    document.title = "Создать документ · SafetyMAIN";
  }, []);

  if (!capabilities.canCreate) {
    return (
      <PageContainer>
        <EmptyState
          title="Нельзя создать документ"
          description="Недостаточно прав для создания документов соответствия."
          action={
            <Button asChild variant="secondary">
              <Link href="/compliance-documents">К реестру</Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  if (typesQuery.isLoading) {
    return (
      <PageContainer>
        <LoadingState label="Загрузка типов документов" />
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

  const activeTypes = typesQuery.data.items.filter((t) => t.is_active);

  async function onSubmit(values: ComplianceDocumentFormValues) {
    try {
      const created = await mutation.mutateAsync(
        formValuesToCreateRequest(values),
      );
      toast({
        tone: "success",
        title: "Документ создан",
        description: created.code,
      });
      router.push(`/compliance-documents/${created.id}`);
    } catch (error) {
      if (error instanceof ConflictError) {
        form.setError("code", {
          message:
            error.message || "Документ с таким кодом уже существует в силе.",
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
        title="Создать документ соответствия"
        description="Новые документы создаются в статусе «Черновик». Файл можно загрузить после создания."
        actions={
          <PageActions>
            <Button asChild variant="secondary">
              <Link href="/compliance-documents">Отмена</Link>
            </Button>
            <Button
              type="submit"
              form="compliance-document-create-form"
              loading={mutation.isPending}
              disabled={mutation.isPending}
            >
              Создать
            </Button>
          </PageActions>
        }
      />

      {form.formState.errors.root?.message ? (
        <Alert tone="danger" title="Не удалось создать документ">
          {form.formState.errors.root.message}
        </Alert>
      ) : null}

      <ComplianceDocumentForm
        id="compliance-document-create-form"
        form={form}
        onSubmit={onSubmit}
        types={activeTypes}
      />
    </PageContainer>
  );
}
