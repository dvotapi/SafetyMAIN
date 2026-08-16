"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  Button,
  Checkbox,
  DatePicker,
  FieldError,
  HelperText,
  Input,
  Label,
  NumberInput,
  Panel,
  Radio,
  RadioGroup,
  ReviewBanner,
  Select,
  Switch,
  Text,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import {
  DEFAULT_COMPLETE_REVIEW_FORM_VALUES,
  DEFAULT_REVIEW_SCHEDULE_FORM_VALUES,
  buildCompleteReviewFormSchema,
  reviewScheduleFormSchema,
  type CompleteReviewFormValues,
  type ReviewScheduleFormValues,
} from "@/features/risk-controls/schemas/review-schema";
import type {
  RiskControlCapabilities,
  RiskControlReviewSchedule,
} from "@/features/risk-controls/types/risk-control-types";
import {
  REVIEW_BASES,
  TERMINAL_INACTIVE_STATUSES,
  VERIFIABLE_RESULTS,
  VERIFICATION_TYPES,
  effectivenessLabel,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly as formatDate } from "@/utils/format-date";

const REVIEW_BASIS_OPTIONS = REVIEW_BASES.map((value) => ({
  value,
  label: formatRiskControlEnumLabel(value),
}));

const VERIFICATION_TYPE_OPTIONS = VERIFICATION_TYPES.map((value) => ({
  value,
  label: formatRiskControlEnumLabel(value),
}));

/**
 * Review scheduling, review completion, and overdue presentation. `Overdue`
 * is read straight from `isOverdue` — never recomputed from `nextReviewDate`
 * client-side, since the domain rule that produces it (e.g. suspended
 * controls are never overdue) is not reproducible on the frontend.
 */
export function ReviewScheduleSection({
  reviewSchedule,
  status,
  version,
  isOverdue,
  capabilities,
  hasExistingEvidence,
  scheduleOpen,
  onScheduleOpenChange,
  completeOpen,
  onCompleteOpenChange,
  onSchedule,
  onComplete,
  scheduleLoading = false,
  completeLoading = false,
  errorMessage = null,
}: {
  reviewSchedule: RiskControlReviewSchedule;
  status: string;
  version: number;
  isOverdue: boolean;
  capabilities: RiskControlCapabilities;
  hasExistingEvidence: boolean;
  scheduleOpen: boolean;
  onScheduleOpenChange: (open: boolean) => void;
  completeOpen: boolean;
  onCompleteOpenChange: (open: boolean) => void;
  onSchedule: (values: ReviewScheduleFormValues) => void | Promise<void>;
  onComplete: (values: CompleteReviewFormValues) => void | Promise<void>;
  scheduleLoading?: boolean;
  completeLoading?: boolean;
  errorMessage?: string | null;
}) {
  const canSchedule =
    capabilities.canReview && !TERMINAL_INACTIVE_STATUSES.has(status);
  const canComplete =
    capabilities.canReview &&
    reviewSchedule.reviewRequired &&
    Boolean(reviewSchedule.nextReviewDate);

  const scheduleForm = useForm<ReviewScheduleFormValues>({
    resolver: zodResolver(reviewScheduleFormSchema),
    defaultValues: DEFAULT_REVIEW_SCHEDULE_FORM_VALUES,
  });

  useEffect(() => {
    if (scheduleOpen) {
      scheduleForm.reset(DEFAULT_REVIEW_SCHEDULE_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scheduleOpen]);

  const completeSchema = useMemo(
    () =>
      buildCompleteReviewFormSchema({
        reviewRequired: reviewSchedule.reviewRequired,
        noReviewReason: reviewSchedule.noReviewReason,
        hasExistingEvidence,
      }),
    [
      reviewSchedule.reviewRequired,
      reviewSchedule.noReviewReason,
      hasExistingEvidence,
    ],
  );

  const completeForm = useForm<CompleteReviewFormValues>({
    resolver: zodResolver(completeSchema),
    defaultValues: DEFAULT_COMPLETE_REVIEW_FORM_VALUES,
  });

  useEffect(() => {
    if (completeOpen) {
      completeForm.reset(DEFAULT_COMPLETE_REVIEW_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [completeOpen]);

  const reviewRequired = scheduleForm.watch("reviewRequired");
  const includeVerification = completeForm.watch("includeVerification");
  const verificationResult = completeForm.watch("verification.result");

  return (
    <>
      {isOverdue ? (
        <ReviewBanner
          message={
            <span style={{ display: "grid", gap: 4 }}>
              <Text as="span" variant="label">
                Пересмотр просрочен
              </Text>
              <Text as="span" variant="caption" tone="muted">
                Запланированная дата пересмотра прошла. Завершите пересмотр,
                чтобы вернуть меру в соответствие.
              </Text>
            </span>
          }
        />
      ) : null}

      <Panel
        heading={<Text variant="label">График пересмотра</Text>}
        actions={
          <div style={{ display: "flex", gap: 8 }}>
            {canSchedule ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onScheduleOpenChange(true)}
              >
                Назначить пересмотр
              </Button>
            ) : null}
            {canComplete ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onCompleteOpenChange(true)}
              >
                Завершить пересмотр
              </Button>
            ) : null}
          </div>
        }
      >
        <div style={{ display: "grid", gap: 4 }}>
          <Text>
            {reviewSchedule.reviewRequired
              ? "Пересмотр требуется"
              : "Пересмотр не требуется"}
          </Text>
          <Text variant="caption" tone="muted">
            Следующий пересмотр: {formatDate(reviewSchedule.nextReviewDate)} ·
            Последний пересмотр: {formatDate(reviewSchedule.lastReviewDate)} ·
            Основание: {formatRiskControlEnumLabel(reviewSchedule.reviewBasis)}
          </Text>
          {!reviewSchedule.reviewRequired && reviewSchedule.noReviewReason ? (
            <Text variant="caption" tone="muted">
              Причина отказа от пересмотра: {reviewSchedule.noReviewReason}
            </Text>
          ) : null}
        </div>
      </Panel>

      <RiskControlCommandDialog
        open={scheduleOpen}
        onOpenChange={onScheduleOpenChange}
        title="Назначить пересмотр"
        version={version}
        errorMessage={errorMessage}
        confirmLabel="Назначить пересмотр"
        loading={scheduleLoading}
        onConfirm={scheduleForm.handleSubmit((values) => onSchedule(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Controller
            control={scheduleForm.control}
            name="reviewRequired"
            render={({ field }) => (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <Switch
                  id="schedule-review-required"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
                <Label htmlFor="schedule-review-required">
                  Пересмотр требуется
                </Label>
              </div>
            )}
          />

          {reviewRequired ? (
            <>
              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="schedule-frequency-days">
                  Частота пересмотра (дней)
                </Label>
                <Controller
                  control={scheduleForm.control}
                  name="reviewFrequencyDays"
                  render={({ field }) => (
                    <NumberInput
                      id="schedule-frequency-days"
                      min={1}
                      step={1}
                      value={field.value ?? ""}
                      onChange={(event) => {
                        const raw = event.target.value;
                        field.onChange(raw === "" ? null : Number(raw));
                      }}
                      invalid={Boolean(
                        scheduleForm.formState.errors.reviewFrequencyDays,
                      )}
                    />
                  )}
                />
                <HelperText>
                  Используется для расчёта даты следующего пересмотра, если она
                  не задана явно ниже.
                </HelperText>
                {scheduleForm.formState.errors.reviewFrequencyDays?.message ? (
                  <FieldError>
                    {scheduleForm.formState.errors.reviewFrequencyDays.message}
                  </FieldError>
                ) : null}
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="schedule-next-review-date">
                  Дата следующего пересмотра
                </Label>
                <DatePicker
                  id="schedule-next-review-date"
                  {...scheduleForm.register("nextReviewDate")}
                />
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="schedule-basis">Основание пересмотра</Label>
                <Controller
                  control={scheduleForm.control}
                  name="reviewBasis"
                  render={({ field }) => (
                    <Select
                      id="schedule-basis"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={REVIEW_BASIS_OPTIONS}
                    />
                  )}
                />
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="schedule-escalation-policy-ref">
                  Ссылка на политику эскалации
                </Label>
                <Input
                  id="schedule-escalation-policy-ref"
                  {...scheduleForm.register("escalationPolicyRef")}
                />
              </div>
            </>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              <Label htmlFor="schedule-no-review-reason" required>
                Причина отказа от пересмотра
              </Label>
              <TextArea
                id="schedule-no-review-reason"
                {...scheduleForm.register("noReviewReason")}
                invalid={Boolean(scheduleForm.formState.errors.noReviewReason)}
              />
              {scheduleForm.formState.errors.noReviewReason?.message ? (
                <FieldError>
                  {scheduleForm.formState.errors.noReviewReason.message}
                </FieldError>
              ) : null}
            </div>
          )}
        </div>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={completeOpen}
        onOpenChange={onCompleteOpenChange}
        title="Завершить пересмотр"
        version={version}
        errorMessage={errorMessage}
        confirmLabel="Завершить пересмотр"
        loading={completeLoading}
        onConfirm={completeForm.handleSubmit((values) => onComplete(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="complete-review-next-review-date">
              Новая дата следующего пересмотра
            </Label>
            <DatePicker
              id="complete-review-next-review-date"
              {...completeForm.register("nextReviewDate")}
            />
            <HelperText>
              Оставьте пустым, чтобы сохранить текущую частоту графика.
            </HelperText>
          </div>

          <Controller
            control={completeForm.control}
            name="includeVerification"
            render={({ field }) => (
              <Checkbox
                id="complete-review-include-verification"
                checked={field.value}
                onCheckedChange={(checked) => field.onChange(checked === true)}
                label="Записать подтверждение в рамках этого пересмотра"
              />
            )}
          />

          {includeVerification ? (
            <div
              style={{
                display: "grid",
                gap: 12,
                paddingLeft: 12,
                borderLeft: "2px solid var(--sm-color-border-default)",
              }}
            >
              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="complete-review-verification-type" required>
                  Тип подтверждения
                </Label>
                <Controller
                  control={completeForm.control}
                  name="verification.verificationType"
                  render={({ field }) => (
                    <Select
                      id="complete-review-verification-type"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={VERIFICATION_TYPE_OPTIONS}
                    />
                  )}
                />
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="complete-review-verification-method" required>
                  Метод
                </Label>
                <Input
                  id="complete-review-verification-method"
                  {...completeForm.register("verification.method")}
                  invalid={Boolean(
                    completeForm.formState.errors.verification?.method,
                  )}
                />
                {completeForm.formState.errors.verification?.method?.message ? (
                  <FieldError>
                    {completeForm.formState.errors.verification.method.message}
                  </FieldError>
                ) : null}
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <Label required>Результат</Label>
                <Controller
                  control={completeForm.control}
                  name="verification.result"
                  render={({ field }) => (
                    <RadioGroup
                      value={field.value}
                      onValueChange={field.onChange}
                      aria-label="Результат"
                    >
                      {VERIFIABLE_RESULTS.map((value) => (
                        <Radio
                          key={value}
                          id={`complete-review-verification-result-${value}`}
                          value={value}
                        >
                          {effectivenessLabel(value)}
                        </Radio>
                      ))}
                    </RadioGroup>
                  )}
                />
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="complete-review-verification-evidence-refs">
                  Ссылки на доказательства
                </Label>
                <Controller
                  control={completeForm.control}
                  name="verification.evidenceRefs"
                  render={({ field }) => (
                    <TextArea
                      id="complete-review-verification-evidence-refs"
                      value={field.value.join("\n")}
                      onChange={(event) =>
                        field.onChange(
                          event.target.value
                            .split("\n")
                            .map((line) => line.trim())
                            .filter((line) => line.length > 0),
                        )
                      }
                      placeholder="По одной ссылке в строке"
                    />
                  )}
                />
                {completeForm.formState.errors.verification?.evidenceRefs
                  ?.message ? (
                  <FieldError>
                    {
                      completeForm.formState.errors.verification.evidenceRefs
                        .message
                    }
                  </FieldError>
                ) : null}
              </div>

              {verificationResult === "partially_effective" ? (
                <Text variant="caption" tone="muted">
                  Partially effective does not change the control&apos;s
                  lifecycle status — only the effectiveness result.
                </Text>
              ) : null}

              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="complete-review-verification-next-review-date">
                  Дата следующего пересмотра по подтверждению
                </Label>
                <Input
                  id="complete-review-verification-next-review-date"
                  type="date"
                  {...completeForm.register("verification.nextReviewDate")}
                  invalid={Boolean(
                    completeForm.formState.errors.verification?.nextReviewDate,
                  )}
                />
                {completeForm.formState.errors.verification?.nextReviewDate
                  ?.message ? (
                  <FieldError>
                    {
                      completeForm.formState.errors.verification.nextReviewDate
                        .message
                    }
                  </FieldError>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </RiskControlCommandDialog>
    </>
  );
}
