"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  Button,
  Checkbox,
  ConfirmationDialog,
  DescriptionItem,
  DescriptionList,
  FieldError,
  HelperText,
  Label,
  NextActionCard,
  NumberInput,
  Panel,
  Text,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import {
  DEFAULT_COMPLETE_IMPLEMENTATION_FORM_VALUES,
  DEFAULT_PROGRESS_FORM_VALUES,
  buildCompleteImplementationFormSchema,
  progressFormSchema,
  type CompleteImplementationFormValues,
  type ProgressFormValues,
} from "@/features/risk-controls/schemas/implementation-progress-schema";
import type {
  RiskControl,
  RiskControlCapabilities,
} from "@/features/risk-controls/types/risk-control-types";
import { formatRiskControlEnumLabel } from "@/features/risk-controls/utils/risk-control-status";

/** A milestone still needs attention while it is neither completed nor cancelled. */
function hasIncompleteMilestone(control: RiskControl): boolean {
  return control.implementation.milestones.some(
    (milestone) =>
      milestone.status !== "completed" && milestone.status !== "cancelled",
  );
}

/**
 * Bundles the three implementation-lifecycle commands that move a control
 * from `planned` through `in_implementation` to `implemented`:
 * `start_implementation`, `update_progress`, and `complete_implementation`.
 * Each command is gated on `capabilities.canImplement` plus the exact
 * status the domain accepts it from — never inferred client-side.
 */
export function ImplementationProgressSection({
  control,
  capabilities,
  startOpen,
  onStartOpenChange,
  progressOpen,
  onProgressOpenChange,
  completeOpen,
  onCompleteOpenChange,
  onStart,
  onProgress,
  onComplete,
  startLoading = false,
  progressLoading = false,
  completeLoading = false,
  errorMessage = null,
}: {
  control: RiskControl;
  capabilities: RiskControlCapabilities;
  startOpen: boolean;
  onStartOpenChange: (open: boolean) => void;
  progressOpen: boolean;
  onProgressOpenChange: (open: boolean) => void;
  completeOpen: boolean;
  onCompleteOpenChange: (open: boolean) => void;
  onStart: () => void | Promise<void>;
  onProgress: (values: ProgressFormValues) => void | Promise<void>;
  onComplete: (
    values: CompleteImplementationFormValues,
  ) => void | Promise<void>;
  startLoading?: boolean;
  progressLoading?: boolean;
  completeLoading?: boolean;
  errorMessage?: string | null;
}) {
  const canStart = capabilities.canImplement && control.status === "planned";
  const canProgress =
    capabilities.canImplement && control.status === "in_implementation";
  const canComplete = canProgress;
  const evidenceIsEmpty = control.evidence.length === 0;
  const showAllowIncompleteMilestones = hasIncompleteMilestone(control);
  const showNextAction = control.status === "implemented";

  const progressDefaultValues = useMemo<ProgressFormValues>(
    () => ({
      progress: control.implementation.progress,
      summary: "",
    }),
    [control.implementation.progress],
  );
  const progressForm = useForm<ProgressFormValues>({
    resolver: zodResolver(progressFormSchema),
    defaultValues: DEFAULT_PROGRESS_FORM_VALUES,
  });
  useEffect(() => {
    if (progressOpen) {
      progressForm.reset(progressDefaultValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progressOpen]);

  const completeSchema = useMemo(
    () => buildCompleteImplementationFormSchema(evidenceIsEmpty),
    [evidenceIsEmpty],
  );
  const completeForm = useForm<CompleteImplementationFormValues>({
    resolver: zodResolver(completeSchema),
    defaultValues: DEFAULT_COMPLETE_IMPLEMENTATION_FORM_VALUES,
  });
  useEffect(() => {
    if (completeOpen) {
      completeForm.reset(DEFAULT_COMPLETE_IMPLEMENTATION_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [completeOpen]);

  return (
    <>
      <Panel
        heading={<Text variant="label">Прогресс внедрения</Text>}
        actions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {canStart ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onStartOpenChange(true)}
              >
                Начать внедрение
              </Button>
            ) : null}
            {canProgress ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onProgressOpenChange(true)}
              >
                Обновить прогресс
              </Button>
            ) : null}
            {canComplete ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onCompleteOpenChange(true)}
              >
                Завершить внедрение
              </Button>
            ) : null}
          </div>
        }
      >
        {showNextAction ? (
          <NextActionCard title="Подтвердить эффективность" />
        ) : (
          <Text tone="muted">
            {canStart
              ? "Начните внедрение, чтобы отслеживать прогресс."
              : canProgress
                ? "Обновляйте прогресс или завершайте внедрение отсюда."
                : "В текущем статусе нет доступных действий по внедрению."}
          </Text>
        )}
      </Panel>

      <ConfirmationDialog
        open={startOpen}
        onOpenChange={onStartOpenChange}
        title="Начать внедрение"
        description={`Начать внедрение ${control.code}? Используется версия ${control.version}.`}
        confirmLabel="Начать внедрение"
        loading={startLoading}
        onConfirm={() => {
          void onStart();
        }}
      />

      <RiskControlCommandDialog
        open={progressOpen}
        onOpenChange={onProgressOpenChange}
        title="Обновить прогресс"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Обновить прогресс"
        loading={progressLoading}
        onConfirm={progressForm.handleSubmit((values) => onProgress(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="progress-value" required>
              Прогресс (%)
            </Label>
            <Controller
              control={progressForm.control}
              name="progress"
              render={({ field }) => (
                <NumberInput
                  id="progress-value"
                  min={0}
                  max={100}
                  step={1}
                  value={Number.isFinite(field.value) ? field.value : ""}
                  onChange={(event) => {
                    const raw = event.target.value;
                    field.onChange(raw === "" ? NaN : Number(raw));
                  }}
                  invalid={Boolean(progressForm.formState.errors.progress)}
                />
              )}
            />
            {progressForm.formState.errors.progress?.message ? (
              <FieldError>
                {progressForm.formState.errors.progress.message}
              </FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="progress-note">Заметка о прогрессе</Label>
            <TextArea
              id="progress-note"
              {...progressForm.register("summary")}
            />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Text variant="label">Вехи</Text>
            {control.implementation.milestones.length > 0 ? (
              <DescriptionList>
                {control.implementation.milestones.map((milestone, index) => (
                  <DescriptionItem
                    key={milestone.id ?? `milestone-${index}`}
                    term={milestone.title}
                    details={formatRiskControlEnumLabel(milestone.status)}
                  />
                ))}
              </DescriptionList>
            ) : (
              <Text tone="muted">Вехи не зафиксированы.</Text>
            )}
            <HelperText>
              Вехи здесь только для чтения — изменяйте их в плане внедрения.
            </HelperText>
          </div>
        </div>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={completeOpen}
        onOpenChange={onCompleteOpenChange}
        title="Завершить внедрение"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Завершить внедрение"
        loading={completeLoading}
        onConfirm={completeForm.handleSubmit((values) => onComplete(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Text tone="secondary">
            Завершение внедрения устанавливает прогресс 100% и делает
            подтверждение эффективности следующим ожидаемым действием.
          </Text>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="complete-summary" required>
              Сводка по завершению
            </Label>
            <TextArea
              id="complete-summary"
              {...completeForm.register("summary")}
              invalid={Boolean(completeForm.formState.errors.summary)}
            />
            {completeForm.formState.errors.summary?.message ? (
              <FieldError>
                {completeForm.formState.errors.summary.message}
              </FieldError>
            ) : null}
          </div>

          {evidenceIsEmpty ? (
            <div style={{ display: "grid", gap: 8 }}>
              <Label htmlFor="complete-evidence-waiver-reason" required>
                Причина отказа от доказательств
              </Label>
              <TextArea
                id="complete-evidence-waiver-reason"
                {...completeForm.register("evidenceWaiverReason")}
                invalid={Boolean(
                  completeForm.formState.errors.evidenceWaiverReason,
                )}
              />
              <HelperText>
                Добавьте хотя бы одну ссылку на доказательство или укажите
                причину отказа.
              </HelperText>
              {completeForm.formState.errors.evidenceWaiverReason?.message ? (
                <FieldError>
                  {completeForm.formState.errors.evidenceWaiverReason.message}
                </FieldError>
              ) : null}
            </div>
          ) : null}

          {showAllowIncompleteMilestones ? (
            <Controller
              control={completeForm.control}
              name="allowIncompleteMilestones"
              render={({ field }) => (
                <Checkbox
                  id="complete-allow-incomplete-milestones"
                  checked={field.value}
                  onCheckedChange={(checked) =>
                    field.onChange(checked === true)
                  }
                  label="Разрешить незавершённые вехи"
                />
              )}
            />
          ) : null}
        </div>
      </RiskControlCommandDialog>
    </>
  );
}
