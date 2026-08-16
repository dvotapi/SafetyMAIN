"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";

import {
  BlockingReason,
  Button,
  FieldError,
  Heading,
  Input,
  Label,
  Panel,
  Select,
  Text,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import {
  DEFAULT_MILESTONE,
  MILESTONE_STATUS_VALUES,
  buildImplementationFormSchema,
  type ImplementationFormValues,
} from "@/features/risk-controls/schemas/implementation-schema";
import type { RiskControlCapabilities } from "@/features/risk-controls/types/risk-control-types";
import { formatRiskControlEnumLabel } from "@/features/risk-controls/utils/risk-control-status";

const MILESTONE_STATUS_OPTIONS = MILESTONE_STATUS_VALUES.map((value) => ({
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

function buildDefaultValues(
  verificationMethodRequirement: string,
): ImplementationFormValues {
  return {
    targetStartDate: "",
    targetCompletionDate: "",
    implementationMethod: "",
    resourceNotes: "",
    dependencies: [],
    evidenceRequirements: [],
    verificationMethodRequirement,
    milestones: [],
  };
}

/**
 * `plan` is only available from `draft` — it transitions the control to
 * `planned`. Edits to an already-planned control's implementation go
 * through `PATCH` (draft/planned only), which is out of scope for this
 * section; this component never renders once `status !== "draft"`.
 */
export function ImplementationPlanSection({
  status,
  ownerAssigned,
  version,
  verificationMethodRequirement,
  capabilities,
  open,
  onOpenChange,
  onPlan,
  loading = false,
  errorMessage = null,
}: {
  status: string;
  ownerAssigned: boolean;
  version: number;
  verificationMethodRequirement: string;
  capabilities: RiskControlCapabilities;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPlan: (values: ImplementationFormValues) => void | Promise<void>;
  loading?: boolean;
  errorMessage?: string | null;
}) {
  const eligibleToPlan = capabilities.canUpdate && status === "draft";
  const canPlan = eligibleToPlan && ownerAssigned;

  const hasExistingVerificationMethodRequirement = Boolean(
    verificationMethodRequirement.trim(),
  );
  const schema = useMemo(
    () => buildImplementationFormSchema(hasExistingVerificationMethodRequirement),
    [hasExistingVerificationMethodRequirement],
  );
  const defaultValues = useMemo(
    () => buildDefaultValues(verificationMethodRequirement),
    [verificationMethodRequirement],
  );

  const form = useForm<ImplementationFormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    if (open) {
      form.reset(defaultValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = form;

  const { fields, append, remove } = useFieldArray({
    control,
    name: "milestones",
  });

  if (!eligibleToPlan) {
    return null;
  }

  return (
    <>
      <Panel
        heading={<Text variant="label">Implementation plan</Text>}
        actions={
          canPlan ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenChange(true)}
            >
              Plan implementation
            </Button>
          ) : null
        }
      >
        {canPlan ? (
          <Text tone="muted">
            No implementation plan yet. Plan implementation to set target
            dates and milestones.
          </Text>
        ) : (
          <BlockingReason>
            Assign an owner before planning implementation.
          </BlockingReason>
        )}
      </Panel>

      <RiskControlCommandDialog
        open={open}
        onOpenChange={onOpenChange}
        title="Plan implementation"
        version={version}
        errorMessage={errorMessage}
        confirmLabel="Plan implementation"
        loading={loading}
        onConfirm={handleSubmit((values) => onPlan(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="plan-target-start-date">
              Target start date
            </Label>
            <Input
              id="plan-target-start-date"
              type="date"
              {...register("targetStartDate")}
              invalid={Boolean(errors.targetStartDate)}
            />
            {errors.targetStartDate?.message ? (
              <FieldError>{errors.targetStartDate.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="plan-target-completion-date" required>
              Target completion date
            </Label>
            <Input
              id="plan-target-completion-date"
              type="date"
              {...register("targetCompletionDate")}
              invalid={Boolean(errors.targetCompletionDate)}
            />
            {errors.targetCompletionDate?.message ? (
              <FieldError>{errors.targetCompletionDate.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="plan-implementation-method">
              Implementation method
            </Label>
            <Input
              id="plan-implementation-method"
              {...register("implementationMethod")}
              invalid={Boolean(errors.implementationMethod)}
            />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="plan-resource-notes">Resource notes</Label>
            <TextArea id="plan-resource-notes" {...register("resourceNotes")} />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="plan-dependencies">Dependencies</Label>
            <Controller
              control={control}
              name="dependencies"
              render={({ field }) => (
                <TextArea
                  id="plan-dependencies"
                  value={arrayToLines(field.value)}
                  onChange={(event) =>
                    field.onChange(linesToArray(event.target.value))
                  }
                />
              )}
            />
            <Text variant="caption" tone="muted">
              One dependency per line.
            </Text>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="plan-evidence-requirements">
              Evidence requirements
            </Label>
            <Controller
              control={control}
              name="evidenceRequirements"
              render={({ field }) => (
                <TextArea
                  id="plan-evidence-requirements"
                  value={arrayToLines(field.value)}
                  onChange={(event) =>
                    field.onChange(linesToArray(event.target.value))
                  }
                />
              )}
            />
            <Text variant="caption" tone="muted">
              One evidence requirement per line.
            </Text>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label
              htmlFor="plan-verification-method-requirement"
              required={!hasExistingVerificationMethodRequirement}
            >
              Verification method requirement
            </Label>
            <Input
              id="plan-verification-method-requirement"
              {...register("verificationMethodRequirement")}
              invalid={Boolean(errors.verificationMethodRequirement)}
            />
            {errors.verificationMethodRequirement?.message ? (
              <FieldError>
                {errors.verificationMethodRequirement.message}
              </FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            <Heading level={3}>Milestones</Heading>
            {fields.map((field, index) => (
              <div
                key={field.id}
                style={{
                  display: "grid",
                  gap: 8,
                  paddingBottom: 12,
                  borderBottom: "1px solid var(--sm-color-border-subtle, #ddd)",
                }}
              >
                <div style={{ display: "grid", gap: 8 }}>
                  <Label htmlFor={`plan-milestone-title-${index}`} required>
                    Title
                  </Label>
                  <Input
                    id={`plan-milestone-title-${index}`}
                    {...register(`milestones.${index}.title`)}
                    invalid={Boolean(errors.milestones?.[index]?.title)}
                  />
                  {errors.milestones?.[index]?.title?.message ? (
                    <FieldError>
                      {errors.milestones[index]?.title?.message}
                    </FieldError>
                  ) : null}
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  <Label htmlFor={`plan-milestone-description-${index}`}>
                    Description
                  </Label>
                  <TextArea
                    id={`plan-milestone-description-${index}`}
                    rows={2}
                    {...register(`milestones.${index}.description`)}
                  />
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  <Label htmlFor={`plan-milestone-due-date-${index}`}>
                    Due date
                  </Label>
                  <Input
                    id={`plan-milestone-due-date-${index}`}
                    type="date"
                    {...register(`milestones.${index}.dueDate`)}
                  />
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  <Label htmlFor={`plan-milestone-status-${index}`}>
                    Status
                  </Label>
                  <Controller
                    control={control}
                    name={`milestones.${index}.status`}
                    render={({ field: statusField }) => (
                      <Select
                        id={`plan-milestone-status-${index}`}
                        value={statusField.value}
                        onValueChange={statusField.onChange}
                        options={MILESTONE_STATUS_OPTIONS}
                      />
                    )}
                  />
                </div>

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => remove(index)}
                >
                  Remove milestone
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => append(DEFAULT_MILESTONE)}
            >
              Add milestone
            </Button>
          </div>
        </div>
      </RiskControlCommandDialog>
    </>
  );
}
