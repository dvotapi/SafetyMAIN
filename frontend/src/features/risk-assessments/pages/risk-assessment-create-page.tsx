"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { useForm, type UseFormSetError } from "react-hook-form";

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
import { invalidateHazardRelatedRiskAssessments } from "@/features/risk-assessments/api/invalidate-hazard-related";
import {
  createRiskAssessment,
  updateRiskAssessment,
} from "@/features/risk-assessments/api/risk-assessment-api";
import { riskAssessmentKeys } from "@/features/risk-assessments/api/risk-assessment-query-keys";
import {
  useRiskAssessmentHazardOptionsQuery,
  useRiskAssessmentHazardQuery,
} from "@/features/risk-assessments/api/risk-assessment-queries";
import { RiskAssessmentForm } from "@/features/risk-assessments/components/risk-assessment-form";
import { mapRiskAssessmentCapabilities } from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import {
  defaultRiskAssessmentFormValues,
  riskAssessmentFormSchema,
  type RiskAssessmentFormValues,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type { RiskAssessment } from "@/features/risk-assessments/types/risk-assessment-types";
import { getAssessmentProfileCatalogEntry } from "@/features/risk-assessments/utils/assessment-profiles";
import {
  orchestrateRiskAssessmentCreate,
  orchestrateRiskAssessmentPatchRetry,
} from "@/features/risk-assessments/utils/create-orchestration";
import { resetEvaluationForProfile } from "@/features/risk-assessments/utils/create-workflow";
import { mapRiskAssessmentValidationDetails } from "@/features/risk-assessments/utils/map-validation-errors";
import { createSubmitLock } from "@/features/risk-assessments/utils/submit-lock";
import { useAuth, useOrganization } from "@/hooks/auth";
import {
  ConflictError,
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

function applyCreateFailure(
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
  if (error instanceof ConflictError) {
    setError("code", {
      message: error.message || "Оценка риска с таким кодом уже существует.",
    });
    return;
  }
  if (error instanceof PermissionError) {
    setError("root", { message: toUserSafeMessage(error) });
    return;
  }
  setError("root", { message: toUserSafeMessage(error) });
}

export function RiskAssessmentCreatePage() {
  const { hasPermission } = useAuth();
  const { organizationId } = useOrganization();
  const capabilities = mapRiskAssessmentCapabilities(hasPermission);
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefillHazardId = searchParams.get("hazardId")?.trim() ?? "";
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [submitting, setSubmitting] = useState(false);
  const [retryingPatch, setRetryingPatch] = useState(false);
  const [partialDraft, setPartialDraft] = useState<RiskAssessment | null>(null);
  const submitLockRef = useRef(createSubmitLock());

  const defaultProfile = defaultRiskAssessmentFormValues.assessmentProfile;
  const defaultFactors =
    getAssessmentProfileCatalogEntry(defaultProfile)?.requiredFactorIds ?? [];

  const form = useForm<RiskAssessmentFormValues>({
    resolver: zodResolver(riskAssessmentFormSchema),
    defaultValues: {
      ...defaultRiskAssessmentFormValues,
      hazardId: prefillHazardId,
      inherentRisk: resetEvaluationForProfile(defaultFactors),
      residualRisk: resetEvaluationForProfile(defaultFactors),
    },
    mode: "onSubmit",
  });

  const hazardOptionsQuery = useRiskAssessmentHazardOptionsQuery(
    "",
    capabilities.canCreate,
  );
  const prefillHazardQuery = useRiskAssessmentHazardQuery(
    prefillHazardId,
    capabilities.canCreate && Boolean(prefillHazardId),
  );

  const hazardOptions = useMemo(() => {
    const items = [...(hazardOptionsQuery.data ?? [])];
    if (
      prefillHazardQuery.data &&
      !items.some((item) => item.id === prefillHazardQuery.data.id)
    ) {
      items.unshift(prefillHazardQuery.data);
    }
    return items;
  }, [hazardOptionsQuery.data, prefillHazardQuery.data]);

  useEffect(() => {
    document.title = "Создать оценку риска · SafetyMAIN";
  }, []);

  useEffect(() => {
    if (prefillHazardId) {
      form.setValue("hazardId", prefillHazardId);
    }
  }, [prefillHazardId, form]);

  if (!capabilities.canCreate) {
    return (
      <PageContainer>
        <EmptyState
          title="Нельзя создать оценки риска"
          description="Недостаточно прав для создания оценок риска."
          action={
            <Button asChild variant="secondary">
              <Link href="/safety/risk-assessments">К реестру</Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  if (hazardOptionsQuery.isLoading && !hazardOptionsQuery.data) {
    return (
      <PageContainer>
        <LoadingState label="Загрузка опасностей" />
      </PageContainer>
    );
  }

  async function invalidateAfterWrite(hazardId: string, assessmentId: string) {
    await queryClient.invalidateQueries({
      queryKey: riskAssessmentKeys.lists(organizationId),
    });
    await queryClient.invalidateQueries({
      queryKey: riskAssessmentKeys.detail(organizationId, assessmentId),
    });
    await invalidateHazardRelatedRiskAssessments(queryClient, {
      organizationId,
      hazardId,
    });
  }

  const apiDeps = {
    create: createRiskAssessment,
    update: updateRiskAssessment,
  };

  async function onSubmit(values: RiskAssessmentFormValues) {
    // After a partial create, Create must not POST again — use Retry instead.
    if (partialDraft) {
      return;
    }
    if (!submitLockRef.current.tryAcquire()) {
      return;
    }
    setSubmitting(true);
    form.clearErrors();
    try {
      const result = await orchestrateRiskAssessmentCreate(values, apiDeps);

      if (result.status === "create_failed") {
        applyCreateFailure(form.setError, result.error);
        submitLockRef.current.release();
        setSubmitting(false);
        return;
      }

      queryClient.setQueryData(
        riskAssessmentKeys.detail(organizationId, result.assessment.id),
        result.assessment,
      );

      if (result.status === "partial_failure") {
        await invalidateAfterWrite(
          result.assessment.hazardId,
          result.assessment.id,
        );
        setPartialDraft(result.assessment);
        toast({
          tone: "warning",
          title: "Черновик создан с неполными данными",
          description:
            "Черновик оценки риска создан, но дополнительные сведения о риске не сохранены. Нажмите «Повторить сохранение сведений о риске» — новый черновик не будет создан.",
        });
        applyCreateFailure(form.setError, result.patchError);
        // Recoverable: allow retry of PATCH (not Create). Keep lock released for retry button.
        submitLockRef.current.release();
        setSubmitting(false);
        return;
      }

      await invalidateAfterWrite(
        result.assessment.hazardId,
        result.assessment.id,
      );
      toast({
        tone: "success",
        title: "Оценка риска создана",
        description: result.assessment.code,
      });
      // Keep submit lock acquired after success so a second click before
      // navigation/unmount cannot create another Draft.
      setSubmitting(true);
      router.push(`/safety/risk-assessments/${result.assessment.id}`);
    } catch (error) {
      applyCreateFailure(form.setError, error);
      submitLockRef.current.release();
      setSubmitting(false);
    }
  }

  async function onRetryPatch() {
    if (!partialDraft || retryingPatch) {
      return;
    }
    const values = form.getValues();
    setRetryingPatch(true);
    form.clearErrors();
    try {
      const result = await orchestrateRiskAssessmentPatchRetry(
        values,
        partialDraft.id,
        partialDraft.version,
        { update: updateRiskAssessment },
      );

      if (result.status === "failed") {
        applyCreateFailure(form.setError, result.error);
        setRetryingPatch(false);
        return;
      }

      queryClient.setQueryData(
        riskAssessmentKeys.detail(organizationId, result.assessment.id),
        result.assessment,
      );
      await invalidateAfterWrite(
        result.assessment.hazardId,
        result.assessment.id,
      );
      setPartialDraft(null);
      toast({
        tone: "success",
        title: "Сведения о риске сохранены",
        description: result.assessment.code,
      });
      // Keep UI busy after success; do not re-enable Create.
      if (!submitLockRef.current.isLocked()) {
        submitLockRef.current.tryAcquire();
      }
      setSubmitting(true);
      router.push(`/safety/risk-assessments/${result.assessment.id}`);
    } catch (error) {
      applyCreateFailure(form.setError, error);
      setRetryingPatch(false);
    }
  }

  const createDisabled = submitting || Boolean(partialDraft);

  return (
    <PageContainer>
      <PageHeader
        title="Создать оценку риска"
        description="Сначала создаётся черновик, затем необязательные сведения о риске сохраняются отдельным обновлением."
        actions={
          <PageActions>
            <Button asChild variant="secondary">
              <Link href="/safety/risk-assessments">Отмена</Link>
            </Button>
            {partialDraft ? (
              <Button
                type="button"
                loading={retryingPatch}
                disabled={retryingPatch}
                onClick={() => {
                  void onRetryPatch();
                }}
              >
                Повторить сохранение сведений о риске
              </Button>
            ) : (
              <Button
                type="submit"
                form="risk-assessment-create-form"
                loading={submitting}
                disabled={createDisabled}
              >
                Создать черновик
              </Button>
            )}
          </PageActions>
        }
      />
      {partialDraft ? (
        <Alert tone="warning" title="Черновик создан с неполными данными">
          Черновик {partialDraft.code} создан, но дополнительные сведения о
          риске не сохранены. Повтор сохраняет только эти сведения и не создаёт
          новый черновик.
        </Alert>
      ) : null}
      {form.formState.errors.root?.message ? (
        <Alert
          tone="danger"
          title={
            partialDraft
              ? "Не удалось сохранить сведения о риске"
              : "Не удалось создать оценку риска"
          }
        >
          {form.formState.errors.root.message}
        </Alert>
      ) : null}
      {prefillHazardId && prefillHazardQuery.isError ? (
        <Alert tone="warning" title="Контекст опасности недоступен">
          Связанную опасность не удалось загрузить. Выберите другую активную
          опасность перед созданием.
        </Alert>
      ) : null}
      <RiskAssessmentForm
        id="risk-assessment-create-form"
        form={form}
        onSubmit={onSubmit}
        hazardOptions={hazardOptions}
        hazardLocked={Boolean(prefillHazardId && prefillHazardQuery.data)}
      />
    </PageContainer>
  );
}
