"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  Alert,
  Button,
  Card,
  EmptyState,
  Heading,
  LoadingState,
  ObjectHeader,
  ObjectTabs,
  StatusBadge,
  Text,
  useToast,
} from "@/components";
import { PageContainer } from "@/components/patterns/Page";

import {
  useActivateComplianceDocumentMutation,
  useApproveComplianceDocumentMutation,
  useArchiveComplianceDocumentMutation,
  useCompleteReviewComplianceDocumentMutation,
  useRestoreComplianceDocumentMutation,
  useStartReviewComplianceDocumentMutation,
} from "@/features/compliance-documents/api/compliance-documents-mutations";
import {
  useComplianceDocumentDetailQuery,
  useComplianceDocumentFileVersionsQuery,
  useDocumentTypesQuery,
} from "@/features/compliance-documents/api/compliance-documents-queries";
import { CompleteReviewDialog } from "@/features/compliance-documents/components/compliance-document-complete-review-dialog";
import { ComplianceDocumentCrosslinks } from "@/features/compliance-documents/components/compliance-document-crosslinks";
import { ComplianceDocumentFilePreview } from "@/features/compliance-documents/components/compliance-document-file-preview";
import {
  ComplianceDocumentLifecycleActions,
  type LifecycleAction,
} from "@/features/compliance-documents/components/compliance-document-lifecycle-actions";
import { ComplianceDocumentProperties } from "@/features/compliance-documents/components/compliance-document-properties";
import { ComplianceDocumentReasonDialog } from "@/features/compliance-documents/components/compliance-document-reason-dialog";
import { ComplianceDocumentStatusBadge } from "@/features/compliance-documents/components/compliance-document-status-badge";
import { ComplianceDocumentUploadDialog } from "@/features/compliance-documents/components/compliance-document-upload-dialog";
import { ComplianceDocumentVersions } from "@/features/compliance-documents/components/compliance-document-versions";
import { mapComplianceDocumentCapabilities } from "@/features/compliance-documents/hooks/use-compliance-document-permissions";
import { shouldShowReviewDueWarning } from "@/features/compliance-documents/utils/status";
import { useAuth } from "@/hooks/auth";
import {
  NotFoundError,
  PermissionError,
  toUserSafeMessage,
} from "@/services/api/errors";

export function ComplianceDocumentObjectPage({
  documentId,
}: {
  documentId: string;
}) {
  const { hasPermission } = useAuth();
  const capabilities = mapComplianceDocumentCapabilities(hasPermission);
  const detail = useComplianceDocumentDetailQuery(
    documentId,
    capabilities.canRead,
  );
  const typesQuery = useDocumentTypesQuery({ enabled: capabilities.canRead });
  const document = detail.data;
  const versions = useComplianceDocumentFileVersionsQuery(
    documentId,
    capabilities.canRead && detail.isSuccess,
  );
  const { toast } = useToast();

  const [tab, setTab] = useState("overview");
  const [busy, setBusy] = useState<LifecycleAction | null>(null);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [restoreOpen, setRestoreOpen] = useState(false);
  const [completeReviewOpen, setCompleteReviewOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);

  const approveMutation = useApproveComplianceDocumentMutation(documentId);
  const activateMutation = useActivateComplianceDocumentMutation(documentId);
  const startReviewMutation =
    useStartReviewComplianceDocumentMutation(documentId);
  const completeReviewMutation =
    useCompleteReviewComplianceDocumentMutation(documentId);
  const archiveMutation = useArchiveComplianceDocumentMutation(documentId);
  const restoreMutation = useRestoreComplianceDocumentMutation(documentId);

  useEffect(() => {
    if (document) {
      window.document.title = `${document.code} · SafetyMAIN`;
    } else {
      window.document.title = "Документ · SafetyMAIN";
    }
  }, [document]);

  async function run<T>(
    action: LifecycleAction,
    exec: () => Promise<T>,
    successTitle: string,
  ): Promise<boolean> {
    setBusy(action);
    setCommandError(null);
    try {
      await exec();
      toast({ tone: "success", title: successTitle });
      return true;
    } catch (cause) {
      setCommandError(toUserSafeMessage(cause));
      return false;
    } finally {
      setBusy(null);
    }
  }

  const activeType = useMemo(
    () =>
      document
        ? typesQuery.data?.items.find((t) => t.id === document.document_type_id)
        : undefined,
    [document, typesQuery.data],
  );

  if (!capabilities.canRead) {
    return (
      <PageContainer variant="object">
        <EmptyState
          title="Документ недоступен"
          description="Недостаточно прав для просмотра документов соответствия."
        />
      </PageContainer>
    );
  }

  if (detail.isLoading) {
    return (
      <PageContainer variant="object">
        <LoadingState label="Загрузка документа" />
      </PageContainer>
    );
  }

  if (detail.isError) {
    if (detail.error instanceof NotFoundError) {
      return (
        <PageContainer variant="object">
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
    if (detail.error instanceof PermissionError) {
      return (
        <PageContainer variant="object">
          <EmptyState
            title="Доступ запрещён"
            description={toUserSafeMessage(detail.error)}
          />
        </PageContainer>
      );
    }
    return (
      <PageContainer variant="object">
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Не удалось загрузить документ">
            {toUserSafeMessage(detail.error)}
          </Alert>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void detail.refetch()}
          >
            Повторить
          </Button>
        </div>
      </PageContainer>
    );
  }

  if (!document) {
    return null;
  }

  const warnReview = shouldShowReviewDueWarning(
    document.status,
    document.is_review_due,
  );

  const tabs = [
    { id: "overview", label: "Обзор" },
    { id: "file", label: "Файл" },
    { id: "versions", label: "Версии" },
    { id: "acknowledgements", label: "Ознакомление" },
    { id: "activity", label: "История" },
  ];

  return (
    <PageContainer variant="object">
      <ObjectHeader
        title={document.title}
        subtitle={document.code}
        status={
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              flexWrap: "wrap",
            }}
          >
            <ComplianceDocumentStatusBadge status={document.status} />
            {warnReview ? (
              <StatusBadge status="overdue" label="Нужен пересмотр" />
            ) : null}
          </div>
        }
        meta={
          <Text tone="muted" variant="caption">
            Версия {document.version}
          </Text>
        }
        actions={
          <div
            style={{
              display: "flex",
              gap: "var(--sm-space-2)",
              flexWrap: "wrap",
            }}
          >
            {document.status === "draft" && capabilities.canUpdate ? (
              <>
                <Button asChild variant="secondary">
                  <Link
                    href={`/compliance-documents/${document.id}/edit`}
                    data-testid="compliance-document-edit-link"
                  >
                    Редактировать
                  </Link>
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setUploadOpen(true)}
                  data-testid="compliance-document-upload-trigger"
                >
                  Загрузить файл
                </Button>
              </>
            ) : null}
            <Button asChild variant="ghost">
              <Link href="/compliance-documents">К реестру</Link>
            </Button>
          </div>
        }
      />

      <ComplianceDocumentLifecycleActions
        document={document}
        capabilities={capabilities}
        busyAction={busy}
        onApprove={() =>
          void run(
            "approve",
            () =>
              approveMutation.mutateAsync({
                expected_version: document.version,
              }),
            "Документ утверждён",
          )
        }
        onActivate={() =>
          void run(
            "activate",
            () =>
              activateMutation.mutateAsync({
                expected_version: document.version,
              }),
            "Документ введён в действие",
          )
        }
        onStartReview={() =>
          void run(
            "start_review",
            () =>
              startReviewMutation.mutateAsync({
                expected_version: document.version,
              }),
            "Пересмотр начат",
          )
        }
        onCompleteReviewOpen={() => setCompleteReviewOpen(true)}
        onArchiveOpen={() => setArchiveOpen(true)}
        onRestoreOpen={() => setRestoreOpen(true)}
      />

      {commandError ? (
        <Alert tone="danger" title="Не удалось выполнить действие">
          {commandError}
        </Alert>
      ) : null}

      <ObjectTabs tabs={tabs} activeTabId={tab} onTabChange={setTab} />

      {tab === "overview" ? (
        <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
          <Card>
            <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
              <Heading level={3}>Свойства</Heading>
              <ComplianceDocumentProperties
                document={document}
                documentType={activeType}
              />
            </div>
          </Card>
          <ComplianceDocumentCrosslinks document={document} />
        </div>
      ) : null}

      {tab === "file" ? (
        <ComplianceDocumentFilePreview
          documentId={document.id}
          currentFile={document.current_file}
          canDownload={capabilities.canRead}
        />
      ) : null}

      {tab === "versions" ? (
        <ComplianceDocumentVersions
          items={versions.data?.items ?? []}
          loading={versions.isLoading}
        />
      ) : null}

      {tab === "acknowledgements" ? (
        <Card>
          <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
            <Heading level={3}>Ознакомление</Heading>
            <Text tone="muted">
              Листы ознакомления и подтверждения появятся в следующих этапах
              эпика P11 (электронные журналы и ПЭП).
            </Text>
          </div>
        </Card>
      ) : null}

      {tab === "activity" ? (
        <Card>
          <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
            <Heading level={3}>История</Heading>
            <Text tone="muted">
              Аудит действий над документом будет подключён в следующем этапе.
            </Text>
          </div>
        </Card>
      ) : null}

      <ComplianceDocumentReasonDialog
        open={archiveOpen}
        onOpenChange={setArchiveOpen}
        title="В архив"
        description={`Документ ${document.code} будет переведён в архив.`}
        confirmLabel="В архив"
        loading={busy === "archive"}
        errorMessage={commandError}
        onConfirm={async (reason) => {
          const ok = await run(
            "archive",
            () =>
              archiveMutation.mutateAsync({
                expected_version: document.version,
                reason,
              }),
            "Документ переведён в архив",
          );
          if (ok) setArchiveOpen(false);
        }}
      />

      <ComplianceDocumentReasonDialog
        open={restoreOpen}
        onOpenChange={setRestoreOpen}
        title="Восстановить из архива"
        description={`Документ ${document.code} будет восстановлен в предыдущий статус.`}
        confirmLabel="Восстановить"
        loading={busy === "restore"}
        errorMessage={commandError}
        onConfirm={async (reason) => {
          const ok = await run(
            "restore",
            () =>
              restoreMutation.mutateAsync({
                expected_version: document.version,
                reason,
              }),
            "Документ восстановлен",
          );
          if (ok) setRestoreOpen(false);
        }}
      />

      <ComplianceDocumentUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        document={document}
      />

      <CompleteReviewDialog
        open={completeReviewOpen}
        onOpenChange={setCompleteReviewOpen}
        loading={busy === "complete_review"}
        errorMessage={commandError}
        onConfirm={async (payload) => {
          const ok = await run(
            "complete_review",
            () =>
              completeReviewMutation.mutateAsync({
                expected_version: document.version,
                completed_on: payload.completed_on,
                ...(payload.next_review_at
                  ? { next_review_at: payload.next_review_at }
                  : {}),
              }),
            "Пересмотр завершён",
          );
          if (ok) setCompleteReviewOpen(false);
        }}
      />
    </PageContainer>
  );
}
