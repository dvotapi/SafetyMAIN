"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  Button,
  FieldError,
  Input,
  Label,
  Panel,
  Radio,
  RadioGroup,
  Select,
  Text,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import {
  DEFAULT_VERIFICATION_FORM_VALUES,
  buildVerificationFormSchema,
  type VerificationFormValues,
} from "@/features/risk-controls/schemas/verification-schema";
import type { RiskControlCapabilities } from "@/features/risk-controls/types/risk-control-types";
import {
  VERIFIABLE_RESULTS,
  VERIFICATION_TYPES,
  VERIFY_ALLOWED_STATUSES,
  effectivenessLabel,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";

const VERIFICATION_TYPE_OPTIONS = VERIFICATION_TYPES.map((value) => ({
  value,
  label: formatRiskControlEnumLabel(value),
}));

function linesToArray(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function arrayToLines(value: string[]): string {
  return value.join("\n");
}

/**
 * Record-verification trigger button and form, combined (mirrors
 * `ImplementationPlanSection`). `result` is a `RadioGroup` over
 * `VERIFIABLE_RESULTS` only — `not_verified` and `not_applicable` always
 * 422 on the backend and are never offered — and each option renders a
 * visible text label (`Подтверждена эффективной`, `Подтверждена частично эффективной`,
 * `Подтверждена неэффективной`), never colour alone. `partially_effective` must
 * never be presented as, or collapse into, either of the other two results.
 */
export function VerificationForm({
  status,
  capabilities,
  reviewRequired,
  noReviewReason,
  hasExistingEvidence,
  version,
  open,
  onOpenChange,
  onSubmit,
  loading = false,
  errorMessage = null,
}: {
  status: string;
  capabilities: RiskControlCapabilities;
  reviewRequired: boolean;
  noReviewReason: string | null;
  hasExistingEvidence: boolean;
  version: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: VerificationFormValues) => void | Promise<void>;
  loading?: boolean;
  errorMessage?: string | null;
}) {
  const canVerify =
    capabilities.canVerify && VERIFY_ALLOWED_STATUSES.has(status);

  const schema = useMemo(
    () =>
      buildVerificationFormSchema({
        reviewRequired,
        noReviewReason,
        hasExistingEvidence,
      }),
    [reviewRequired, noReviewReason, hasExistingEvidence],
  );

  const form = useForm<VerificationFormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULT_VERIFICATION_FORM_VALUES,
  });

  useEffect(() => {
    if (open) {
      form.reset(DEFAULT_VERIFICATION_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const {
    control,
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = form;

  const result = watch("result");

  if (!canVerify) {
    return null;
  }

  return (
    <>
      <Panel
        heading={<Text variant="label">Записать подтверждение</Text>}
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onOpenChange(true)}
          >
            Записать подтверждение
          </Button>
        }
      >
        <Text variant="caption" tone="muted">
          Частичная эффективность не меняет статус жизненного цикла — только
          результат эффективности.
        </Text>
      </Panel>

      <RiskControlCommandDialog
        open={open}
        onOpenChange={onOpenChange}
        title="Записать подтверждение"
        version={version}
        errorMessage={errorMessage}
        confirmLabel="Записать подтверждение"
        loading={loading}
        onConfirm={handleSubmit((values) => onSubmit(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-type" required>
              Тип подтверждения
            </Label>
            <Controller
              control={control}
              name="verificationType"
              render={({ field }) => (
                <Select
                  id="verification-type"
                  value={field.value}
                  onValueChange={field.onChange}
                  options={VERIFICATION_TYPE_OPTIONS}
                  invalid={Boolean(errors.verificationType)}
                />
              )}
            />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-method" required>
              Метод
            </Label>
            <Input
              id="verification-method"
              {...register("method")}
              invalid={Boolean(errors.method)}
            />
            {errors.method?.message ? (
              <FieldError>{errors.method.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-criteria">Критерии</Label>
            <TextArea id="verification-criteria" {...register("criteria")} />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label required>Результат</Label>
            <Controller
              control={control}
              name="result"
              render={({ field }) => (
                <RadioGroup
                  value={field.value}
                  onValueChange={field.onChange}
                  aria-label="Результат"
                >
                  {VERIFIABLE_RESULTS.map((value) => (
                    <Radio
                      key={value}
                      id={`verification-result-${value}`}
                      value={value}
                    >
                      {effectivenessLabel(value)}
                    </Radio>
                  ))}
                </RadioGroup>
              )}
            />
            {errors.result?.message ? (
              <FieldError>{errors.result.message}</FieldError>
            ) : null}
          </div>

          {result === "partially_effective" ? (
            <Text variant="caption" tone="muted">
              Частичная эффективность не меняет статус жизненного цикла — только
              результат эффективности.
            </Text>
          ) : null}

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-rating">Оценка</Label>
            <Input id="verification-rating" {...register("rating")} />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-findings">Выводы</Label>
            <TextArea id="verification-findings" {...register("findings")} />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-evidence-refs">
              Ссылки на доказательства
            </Label>
            <Controller
              control={control}
              name="evidenceRefs"
              render={({ field }) => (
                <TextArea
                  id="verification-evidence-refs"
                  value={arrayToLines(field.value)}
                  onChange={(event) =>
                    field.onChange(linesToArray(event.target.value))
                  }
                  placeholder="По одной ссылке в строке"
                />
              )}
            />
            {errors.evidenceRefs?.message ? (
              <FieldError>{errors.evidenceRefs.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-next-action">
              Рекомендация / следующее действие
            </Label>
            <TextArea
              id="verification-next-action"
              {...register("nextAction")}
            />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="verification-next-review-date">
              Дата следующего пересмотра
            </Label>
            <Input
              id="verification-next-review-date"
              type="date"
              {...register("nextReviewDate")}
              invalid={Boolean(errors.nextReviewDate)}
            />
            {errors.nextReviewDate?.message ? (
              <FieldError>{errors.nextReviewDate.message}</FieldError>
            ) : null}
          </div>
        </div>
      </RiskControlCommandDialog>
    </>
  );
}
