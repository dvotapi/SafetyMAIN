"use client";

import { useMemo } from "react";
import {
  Controller,
  useFieldArray,
  useWatch,
  type UseFormReturn,
} from "react-hook-form";

import {
  Button,
  FieldError,
  Form,
  FormRow,
  FormSection,
  Input,
  Label,
  Select,
  TextArea,
  ValidationSummary,
} from "@/components";
import {
  ASSESSED_OBJECT_TYPES,
  ACCEPTANCE_DECISIONS,
  ASSESSMENT_PROFILES,
  CONTROL_TYPES,
  type RiskAssessmentFormValues,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type { RiskAssessmentHazardSummary } from "@/features/risk-assessments/types/risk-assessment-types";
import {
  ASSESSMENT_PROFILE_CATALOG,
  extraFactorIds,
  getAssessmentProfileCatalogEntry,
} from "@/features/risk-assessments/utils/assessment-profiles";
import { controlTypeLabel } from "@/features/risk-assessments/utils/hierarchy-of-controls";
import { formatRiskAssessmentEnumLabel } from "@/features/risk-assessments/utils/risk-assessment-status";
import { resetEvaluationForProfile } from "@/features/risk-assessments/utils/create-workflow";

function enumOptions(values: readonly string[]) {
  return values.map((value) => ({
    value,
    label: formatRiskAssessmentEnumLabel(value),
  }));
}

function RiskEvaluationFields({
  form,
  section,
  maxScore,
  extraFactors,
  readOnly,
}: {
  form: UseFormReturn<RiskAssessmentFormValues>;
  section: "inherentRisk" | "residualRisk";
  maxScore: number;
  extraFactors: readonly string[];
  readOnly?: boolean;
}) {
  const {
    register,
    control,
    formState: { errors },
  } = form;
  const sectionErrors = errors[section];
  const scoreOptions = Array.from({ length: maxScore }, (_, index) => {
    const value = String(index + 1);
    return { value, label: value };
  });

  return (
    <>
      <FormRow>
        <Label htmlFor={`${section}-probability`} required>
          Probability (1–{maxScore})
        </Label>
        <Controller
          control={control}
          name={`${section}.probabilityScore`}
          render={({ field }) => (
            <Select
              id={`${section}-probability`}
              value={field.value === null ? "" : String(field.value)}
              onValueChange={(value) =>
                field.onChange(value === "" ? null : Number.parseInt(value, 10))
              }
              options={[{ value: "", label: "Not set" }, ...scoreOptions]}
              disabled={Boolean(readOnly)}
              invalid={Boolean(sectionErrors?.probabilityScore)}
            />
          )}
        />
        {sectionErrors?.probabilityScore?.message ? (
          <FieldError>{sectionErrors.probabilityScore.message}</FieldError>
        ) : null}
      </FormRow>
      <FormRow>
        <Label htmlFor={`${section}-severity`} required>
          Severity (1–{maxScore})
        </Label>
        <Controller
          control={control}
          name={`${section}.severityScore`}
          render={({ field }) => (
            <Select
              id={`${section}-severity`}
              value={field.value === null ? "" : String(field.value)}
              onValueChange={(value) =>
                field.onChange(value === "" ? null : Number.parseInt(value, 10))
              }
              options={[{ value: "", label: "Not set" }, ...scoreOptions]}
              disabled={Boolean(readOnly)}
              invalid={Boolean(sectionErrors?.severityScore)}
            />
          )}
        />
        {sectionErrors?.severityScore?.message ? (
          <FieldError>{sectionErrors.severityScore.message}</FieldError>
        ) : null}
      </FormRow>
      {extraFactors.map((factorId) => (
        <FormRow key={`${section}-${factorId}`}>
          <Label htmlFor={`${section}-${factorId}`} required>
            {formatRiskAssessmentEnumLabel(factorId)} (1–{maxScore})
          </Label>
          <Controller
            control={control}
            name={`${section}.extraFactorScores.${factorId}`}
            render={({ field }) => (
              <Select
                id={`${section}-${factorId}`}
                value={
                  field.value === null || field.value === undefined
                    ? ""
                    : String(field.value)
                }
                onValueChange={(value) =>
                  field.onChange(
                    value === "" ? null : Number.parseInt(value, 10),
                  )
                }
                options={[{ value: "", label: "Not set" }, ...scoreOptions]}
                disabled={Boolean(readOnly)}
                invalid={Boolean(
                  sectionErrors?.extraFactorScores?.[factorId as never],
                )}
              />
            )}
          />
          {sectionErrors?.extraFactorScores?.[factorId as never]?.message ? (
            <FieldError>
              {
                sectionErrors.extraFactorScores[factorId as never]
                  ?.message as string
              }
            </FieldError>
          ) : null}
        </FormRow>
      ))}
      <FormRow>
        <Label htmlFor={`${section}-explanation`}>Explanation</Label>
        <TextArea
          id={`${section}-explanation`}
          rows={3}
          {...register(`${section}.explanation`)}
          disabled={Boolean(readOnly)}
        />
      </FormRow>
    </>
  );
}

export function RiskAssessmentForm({
  form,
  onSubmit,
  id = "risk-assessment-form",
  readOnly = false,
  hazardOptions,
  hazardLocked = false,
  /** Locks create-only identity fields (hazard, code, profile) for draft edit. */
  identityLocked = false,
}: {
  form: UseFormReturn<RiskAssessmentFormValues>;
  onSubmit: (values: RiskAssessmentFormValues) => void;
  id?: string;
  readOnly?: boolean;
  hazardOptions: RiskAssessmentHazardSummary[];
  hazardLocked?: boolean;
  identityLocked?: boolean;
}) {
  const identityDisabled = Boolean(readOnly || identityLocked);
  const {
    register,
    control,
    setValue,
    formState: { errors },
  } = form;
  const { fields, append, remove } = useFieldArray({
    control,
    name: "controls",
  });
  const profileCode = useWatch({ control, name: "assessmentProfile" });
  const profile = getAssessmentProfileCatalogEntry(profileCode);
  const maxScore = profile?.matrixSize ?? 5;
  const extras = useMemo(
    () => (profile ? extraFactorIds(profile) : []),
    [profile],
  );

  const summaryErrors = Object.values(errors)
    .flatMap((error) => {
      if (!error) {
        return [];
      }
      if (typeof error.message === "string") {
        return [error.message];
      }
      return [];
    })
    .filter(Boolean);

  return (
    <Form form={form} onSubmit={onSubmit} id={id}>
      {summaryErrors.length > 0 ? (
        <ValidationSummary errors={summaryErrors} />
      ) : null}

      <FormSection title="Assessment identity">
        <FormRow>
          <Label htmlFor="ra-hazard" required>
            Hazard
          </Label>
          <Controller
            control={control}
            name="hazardId"
            render={({ field }) => (
              <Select
                id="ra-hazard"
                value={field.value}
                onValueChange={field.onChange}
                options={[
                  { value: "", label: "Select hazard" },
                  ...hazardOptions.map((hazard) => ({
                    value: hazard.id,
                    label: `${hazard.code} — ${hazard.title}`,
                  })),
                ]}
                disabled={Boolean(readOnly || hazardLocked || identityLocked)}
                invalid={Boolean(errors.hazardId)}
              />
            )}
          />
          {errors.hazardId?.message ? (
            <FieldError>{errors.hazardId.message}</FieldError>
          ) : null}
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-code" required>
            Code
          </Label>
          <Input
            id="ra-code"
            {...register("code")}
            disabled={identityDisabled}
            invalid={Boolean(errors.code)}
            autoComplete="off"
          />
          {errors.code?.message ? (
            <FieldError>{errors.code.message}</FieldError>
          ) : null}
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-title" required>
            Title
          </Label>
          <Input
            id="ra-title"
            {...register("title")}
            disabled={Boolean(readOnly)}
            invalid={Boolean(errors.title)}
          />
          {errors.title?.message ? (
            <FieldError>{errors.title.message}</FieldError>
          ) : null}
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-profile" required>
            Assessment profile
          </Label>
          <Controller
            control={control}
            name="assessmentProfile"
            render={({ field }) => (
              <Select
                id="ra-profile"
                value={field.value}
                onValueChange={(value) => {
                  const next =
                    value as RiskAssessmentFormValues["assessmentProfile"];
                  const entry = getAssessmentProfileCatalogEntry(next);
                  const factorIds = entry?.requiredFactorIds ?? [];
                  if (
                    typeof window !== "undefined" &&
                    field.value !== next &&
                    !window.confirm(
                      "Changing the assessment profile clears entered risk scores. Continue?",
                    )
                  ) {
                    return;
                  }
                  field.onChange(next);
                  setValue(
                    "inherentRisk",
                    resetEvaluationForProfile(factorIds),
                  );
                  setValue(
                    "residualRisk",
                    resetEvaluationForProfile(factorIds),
                  );
                }}
                options={ASSESSMENT_PROFILES.map((code) => ({
                  value: code,
                  label:
                    ASSESSMENT_PROFILE_CATALOG.find(
                      (item) => item.code === code,
                    )?.title ?? code,
                }))}
                disabled={identityDisabled}
                invalid={Boolean(errors.assessmentProfile)}
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-object-type" required>
            Assessed object type
          </Label>
          <Controller
            control={control}
            name="assessedObjectType"
            render={({ field }) => (
              <Select
                id="ra-object-type"
                value={field.value}
                onValueChange={field.onChange}
                options={enumOptions(ASSESSED_OBJECT_TYPES)}
                disabled={Boolean(readOnly)}
                invalid={Boolean(errors.assessedObjectType)}
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-object-ref" required>
            Assessed object reference
          </Label>
          <Input
            id="ra-object-ref"
            {...register("assessedObjectReference")}
            disabled={Boolean(readOnly)}
            invalid={Boolean(errors.assessedObjectReference)}
          />
          {errors.assessedObjectReference?.message ? (
            <FieldError>{errors.assessedObjectReference.message}</FieldError>
          ) : null}
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-assessment-date">Assessment date</Label>
          <Input
            id="ra-assessment-date"
            type="date"
            {...register("assessmentDate")}
            disabled={Boolean(readOnly)}
          />
        </FormRow>
      </FormSection>

      <FormSection title="Review schedule (optional)">
        <FormRow>
          <Label htmlFor="ra-review-due">Review due date</Label>
          <Input
            id="ra-review-due"
            type="date"
            {...register("reviewDueDate")}
            disabled={Boolean(readOnly)}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-review-frequency">Review frequency (days)</Label>
          <Input
            id="ra-review-frequency"
            inputMode="numeric"
            {...register("reviewFrequencyDays")}
            disabled={Boolean(readOnly)}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-review-reason">Review reason</Label>
          <Input
            id="ra-review-reason"
            {...register("reviewReason")}
            disabled={Boolean(readOnly)}
          />
        </FormRow>
      </FormSection>

      <FormSection
        title="Competency requirements (optional)"
        description="One requirement per line."
      >
        <FormRow>
          <Label htmlFor="ra-competency">Requirements</Label>
          <TextArea
            id="ra-competency"
            rows={3}
            value={form.watch("competencyRequirements").join("\n")}
            onChange={(event) => {
              const lines = event.target.value
                .split("\n")
                .map((line) => line.trim())
                .filter(Boolean);
              setValue("competencyRequirements", lines, {
                shouldDirty: true,
                shouldValidate: true,
              });
            }}
            disabled={Boolean(readOnly)}
          />
        </FormRow>
      </FormSection>

      <FormSection
        title="Inherent risk"
        description="Optional on create. Saved with a follow-up update after the draft is created. Risk level is calculated by the server."
      >
        <RiskEvaluationFields
          form={form}
          section="inherentRisk"
          maxScore={maxScore}
          extraFactors={extras}
          readOnly={readOnly}
        />
      </FormSection>

      <FormSection title="Proposed controls (optional)">
        {fields.map((field, index) => (
          <div
            key={field.id}
            style={{
              display: "grid",
              gap: 12,
              paddingBottom: 12,
              borderBottom: "1px solid var(--sm-color-border-subtle, #ddd)",
            }}
          >
            <FormRow>
              <Label htmlFor={`ra-control-type-${index}`} required>
                Control type
              </Label>
              <Controller
                control={control}
                name={`controls.${index}.controlType`}
                render={({ field: controlField }) => (
                  <Select
                    id={`ra-control-type-${index}`}
                    value={controlField.value}
                    onValueChange={controlField.onChange}
                    options={CONTROL_TYPES.map((value) => ({
                      value,
                      label: controlTypeLabel(value),
                    }))}
                    disabled={Boolean(readOnly)}
                  />
                )}
              />
            </FormRow>
            <FormRow>
              <Label htmlFor={`ra-control-desc-${index}`} required>
                Description
              </Label>
              <TextArea
                id={`ra-control-desc-${index}`}
                rows={2}
                {...register(`controls.${index}.description`)}
                disabled={Boolean(readOnly)}
              />
            </FormRow>
            <FormRow>
              <Label htmlFor={`ra-control-responsible-${index}`}>
                Responsible
              </Label>
              <Input
                id={`ra-control-responsible-${index}`}
                {...register(`controls.${index}.responsible`)}
                disabled={Boolean(readOnly)}
              />
            </FormRow>
            {!readOnly ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => remove(index)}
              >
                Remove control
              </Button>
            ) : null}
          </div>
        ))}
        {!readOnly ? (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() =>
              append({
                id: null,
                controlType: "administrative",
                description: "",
                responsible: "",
                implemented: false,
                effective: null,
              })
            }
          >
            Add proposed control
          </Button>
        ) : null}
      </FormSection>

      <FormSection
        title="Residual risk"
        description="Optional. Enter after proposed controls when applicable."
      >
        <RiskEvaluationFields
          form={form}
          section="residualRisk"
          maxScore={maxScore}
          extraFactors={extras}
          readOnly={readOnly}
        />
      </FormSection>

      <FormSection title="Acceptance (optional)">
        <FormRow>
          <Label htmlFor="ra-acceptance">Decision</Label>
          <Controller
            control={control}
            name="acceptanceDecision"
            render={({ field }) => (
              <Select
                id="ra-acceptance"
                value={field.value ?? ""}
                onValueChange={(value) =>
                  field.onChange(value === "" ? null : value)
                }
                options={[
                  { value: "", label: "Not set" },
                  ...ACCEPTANCE_DECISIONS.map((value) => ({
                    value,
                    label: formatRiskAssessmentEnumLabel(value),
                  })),
                ]}
                disabled={Boolean(readOnly)}
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="ra-acceptance-justification">Justification</Label>
          <TextArea
            id="ra-acceptance-justification"
            rows={3}
            {...register("acceptanceJustification")}
            disabled={Boolean(readOnly)}
          />
        </FormRow>
      </FormSection>
    </Form>
  );
}
