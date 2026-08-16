"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useForm, type UseFormSetError } from "react-hook-form";

import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
  ObjectHeader,
  ObjectTabs,
  SideDrawer,
  StatusBadge,
  Text,
  useToast,
} from "@/components";
import { PageContainer } from "@/components/patterns/Page";
import {
  useApproveRiskAssessmentMutation,
  useArchiveRiskAssessmentMutation,
  useUpdateRiskAssessmentMutation,
} from "@/features/risk-assessments/api/risk-assessment-mutations";
import {
  useRelatedRiskControlsQuery,
  useRiskAssessmentActivityQuery,
  useRiskAssessmentDetailQuery,
  useRiskAssessmentHazardQuery,
} from "@/features/risk-assessments/api/risk-assessment-queries";
import { RiskAssessmentActivity } from "@/features/risk-assessments/components/risk-assessment-activity";
import { RiskAssessmentConflictDialog } from "@/features/risk-assessments/components/risk-assessment-conflict-dialog";
import { RiskAssessmentForm } from "@/features/risk-assessments/components/risk-assessment-form";
import {
  RiskAssessmentLifecycleActions,
  type ApproveAcceptanceInput,
} from "@/features/risk-assessments/components/risk-assessment-lifecycle-actions";
import { RiskAssessmentRelatedControls } from "@/features/risk-assessments/components/risk-assessment-related-controls";
import {
  RiskAssessmentProperties,
  RiskAssessmentSummary,
} from "@/features/risk-assessments/components/risk-assessment-summary";
import {
  canEditRiskAssessmentFields,
  mapRiskAssessmentCapabilities,
} from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import {
  formValuesToUpdateRequest,
  riskAssessmentToFormValues,
} from "@/features/risk-assessments/mappers/risk-assessment-mappers";
import {
  riskAssessmentFormSchema,
  type RiskAssessmentFormValues,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type { RiskAssessmentLifecycleAction } from "@/features/risk-assessments/types/risk-assessment-types";
import { mapRiskAssessmentValidationDetails } from "@/features/risk-assessments/utils/map-validation-errors";
import { riskAssessmentStatusToVisual } from "@/features/risk-assessments/utils/risk-assessment-status";
import { MaterializeControlsDialog } from "@/features/risk-controls";
import { useAuth } from "@/hooks/auth";
import {
  ConflictError,
  NotFoundError,
  PermissionError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

function applyMappedValidationErrors(
  setError: UseFormSetError<RiskAssessmentFormValues>,
  details: unknown,
  fallbackMessage: string,
): void {
  const mapped = mapRiskAssessmentValidationDetails(details, fallbackMessage);
  for (const fieldError of mapped.fieldErrors) {
    setError(fieldError.name, { message: fieldError.message });
  }
  if (mapped.rootMessage) {
    setError("root", { message: mapped.rootMessage });
  }
}

function applyMutationFailure(
  setError: UseFormSetError<RiskAssessmentFormValues>,
  error: unknown,
): void {
  if (error instanceof ValidationError) {
    applyMappedValidationErrors(
      setError,
      error.details,
      error.message || "Ошибка проверки данных.",
    );
    return;
  }
  setError("root", { message: toUserSafeMessage(error) });
}

export function RiskAssessmentObjectPage({
  riskAssessmentId,
}: {
  riskAssessmentId: string;
}) {
  const { hasPermission } = useAuth();
  const capabilities = mapRiskAssessmentCapabilities(hasPermission);
  const { toast } = useToast();
  const detail = useRiskAssessmentDetailQuery(
    riskAssessmentId,
    capabilities.canRead,
  );
  const relatedControls = useRelatedRiskControlsQuery(
    riskAssessmentId,
    capabilities.canViewRelatedControls && detail.isSuccess,
  );
  const activity = useRiskAssessmentActivityQuery(
    riskAssessmentId,
    capabilities.canViewActivity && detail.isSuccess,
  );
  const updateMutation = useUpdateRiskAssessmentMutation(riskAssessmentId);
  const approveMutation = useApproveRiskAssessmentMutation(riskAssessmentId);
  const archiveMutation = useArchiveRiskAssessmentMutation(riskAssessmentId);

  const [tab, setTab] = useState("overview");
  const [editOpen, setEditOpen] = useState(false);
  const [materializeOpen, setMaterializeOpen] = useState(false);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [lifecycleError, setLifecycleError] = useState<string | null>(null);
  const [busyAction, setBusyAction] =
    useState<RiskAssessmentLifecycleAction | null>(null);

  const form = useForm<RiskAssessmentFormValues>({
    resolver: zodResolver(riskAssessmentFormSchema),
    mode: "onSubmit",
  });

  const assessment = detail.data;
  const hazardQuery = useRiskAssessmentHazardQuery(
    assessment?.hazardId ?? "",
    Boolean(assessment?.hazardId),
  );

  useEffect(() => {
    if (assessment) {
      document.title = `${assessment.code} · SafetyMAIN`;
    } else {
      document.title = "Оценка риска · SafetyMAIN";
    }
  }, [assessment]);

  useEffect(() => {
    if (assessment && editOpen) {
      form.reset(riskAssessmentToFormValues(assessment));
    }
  }, [assessment, editOpen, form]);

  const editable = useMemo(
    () =>
      assessment
        ? canEditRiskAssessmentFields(assessment, capabilities)
        : false,
    [assessment, capabilities],
  );

  const hazardOptions = useMemo(() => {
    if (!assessment) {
      return [];
    }
    if (hazardQuery.data) {
      return [hazardQuery.data];
    }
    return [
      {
        id: assessment.hazardId,
        code: assessment.hazardId,
        title: "Связанная опасность",
        status: "unknown",
      },
    ];
  }, [assessment, hazardQuery.data]);

  if (!capabilities.canRead) {
    return (
      <PageContainer variant="object">
        <EmptyState
          title="Оценка риска недоступна"
          description="Недостаточно прав для просмотра оценок риска."
        />
      </PageContainer>
    );
  }

  if (detail.isLoading) {
    return (
      <PageContainer variant="object">
        <LoadingState label="Загрузка оценки риска" />
      </PageContainer>
    );
  }

  if (detail.isError) {
    if (detail.error instanceof NotFoundError) {
      return (
        <PageContainer variant="object">
          <EmptyState
            title="Оценка риска не найдена"
            description="Эта оценка не существует или недоступна в активной организации."
            action={
              <Button asChild variant="secondary">
                <Link href="/safety/risk-assessments">К реестру</Link>
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
          <Alert tone="danger" title="Не удалось загрузить оценку риска">
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

  if (!assessment) {
    return null;
  }

  async function onSave(values: RiskAssessmentFormValues) {
    if (!assessment) {
      return;
    }
    try {
      await updateMutation.mutateAsync(
        formValuesToUpdateRequest(values, assessment.version, {
          includeRiskInputs: true,
        }),
      );
      toast({ tone: "success", title: "Оценка риска обновлена" });
      setEditOpen(false);
    } catch (error) {
      if (error instanceof ConflictError) {
        setConflictOpen(true);
        return;
      }
      applyMutationFailure(form.setError, error);
    }
  }

  async function runLifecycle(
    action: RiskAssessmentLifecycleAction,
    runner: () => Promise<unknown>,
    successTitle: string,
    successDescription?: string,
  ): Promise<boolean> {
    setLifecycleError(null);
    setBusyAction(action);
    try {
      await runner();
      toast({
        tone: "success",
        title: successTitle,
        ...(successDescription ? { description: successDescription } : {}),
      });
      void detail.refetch();
      void activity.refetch();
      void relatedControls.refetch();
      return true;
    } catch (error) {
      if (error instanceof ConflictError) {
        setConflictOpen(true);
      } else if (error instanceof ValidationError) {
        const mapped = mapRiskAssessmentValidationDetails(
          error.details,
          error.message || "Ошибка проверки данных.",
        );
        setLifecycleError(
          [
            ...mapped.fieldErrors.map(
              (item) => `${String(item.name)}: ${item.message}`,
            ),
            mapped.rootMessage,
          ]
            .filter(Boolean)
            .join("; ") || toUserSafeMessage(error),
        );
      } else {
        setLifecycleError(toUserSafeMessage(error));
      }
      return false;
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <PageContainer variant="object">
      <ObjectHeader
        title={assessment.title}
        subtitle={assessment.code}
        status={
          <StatusBadge
            status={riskAssessmentStatusToVisual(assessment.status)}
          />
        }
        meta={
          <Text tone="muted" variant="caption">
            Версия {assessment.version}
          </Text>
        }
        actions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {editable ? (
              <Button variant="secondary" onClick={() => setEditOpen(true)}>
                Изменить черновик
              </Button>
            ) : null}
            <Button asChild variant="ghost">
              <Link href="/safety/risk-assessments">К реестру</Link>
            </Button>
          </div>
        }
      />

      <RiskAssessmentSummary assessment={assessment} />
      <RiskAssessmentLifecycleActions
        assessment={assessment}
        capabilities={capabilities}
        busyAction={busyAction}
        errorMessage={lifecycleError}
        onSubmitForReview={() =>
          runLifecycle(
            "submit_for_review",
            () =>
              updateMutation.mutateAsync({
                expected_version: assessment.version,
                submit_for_review: true,
              }),
            "Отправлено на рассмотрение",
          )
        }
        onApprove={(acceptance: ApproveAcceptanceInput) =>
          runLifecycle(
            "approve",
            () =>
              approveMutation.mutateAsync({
                expected_version: assessment.version,
                acceptance: {
                  decision: acceptance.decision,
                  justification: acceptance.justification,
                },
              }),
            "Оценка риска утверждена",
            "Если в той же области уже была утверждённая оценка, она могла быть замещена. Списки и карточки обновлены.",
          )
        }
        onArchive={(reason) =>
          runLifecycle(
            "archive",
            () =>
              archiveMutation.mutateAsync({
                expected_version: assessment.version,
                reason,
              }),
            "Оценка риска архивирована",
          )
        }
      />

      <ObjectTabs
        tabs={[
          { id: "overview", label: "Обзор" },
          { id: "controls", label: "Связанные меры" },
          { id: "activity", label: "История" },
        ]}
        activeTabId={tab}
        onTabChange={setTab}
      />

      {tab === "overview" ? (
        <RiskAssessmentProperties
          assessment={assessment}
          relatedHazard={hazardQuery.data ?? null}
        />
      ) : null}

      {tab === "controls" ? (
        <RiskAssessmentRelatedControls
          proposedControls={assessment.controls}
          controls={relatedControls.data ?? []}
          loading={relatedControls.isLoading}
          canView={capabilities.canViewRelatedControls}
          actions={
            <MaterializeControlsDialog
              riskAssessmentId={riskAssessmentId}
              assessmentStatus={assessment.status}
              proposedControls={assessment.controls}
              open={materializeOpen}
              onOpenChange={setMaterializeOpen}
              onSuccess={() => {
                void relatedControls.refetch();
              }}
            />
          }
        />
      ) : null}

      {tab === "activity" ? (
        <RiskAssessmentActivity
          items={activity.data ?? []}
          loading={activity.isLoading}
          canView={capabilities.canViewActivity}
        />
      ) : null}

      <SideDrawer
        open={editOpen}
        onOpenChange={setEditOpen}
        title="Изменить черновик"
        description="Опасность, код и профиль нельзя изменить после создания."
      >
        {form.formState.errors.root?.message ? (
          <Alert tone="danger" title="Не удалось обновить оценку риска">
            {form.formState.errors.root.message}
          </Alert>
        ) : null}
        <RiskAssessmentForm
          id="risk-assessment-edit-form"
          form={form}
          onSubmit={onSave}
          hazardOptions={hazardOptions}
          hazardLocked
          identityLocked
        />
        <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
          <Button variant="secondary" onClick={() => setEditOpen(false)}>
            Отмена
          </Button>
          <Button
            type="submit"
            form="risk-assessment-edit-form"
            loading={updateMutation.isPending}
            disabled={updateMutation.isPending}
          >
            Сохранить изменения
          </Button>
        </div>
      </SideDrawer>

      <RiskAssessmentConflictDialog
        open={conflictOpen}
        onOpenChange={setConflictOpen}
        loading={detail.isFetching}
        onReload={() => {
          void detail.refetch();
        }}
      />
    </PageContainer>
  );
}
