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
  onComplete: (values: CompleteImplementationFormValues) => void | Promise<void>;
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
        heading={<Text variant="label">Implementation progress</Text>}
        actions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {canStart ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onStartOpenChange(true)}
              >
                Start implementation
              </Button>
            ) : null}
            {canProgress ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onProgressOpenChange(true)}
              >
                Update progress
              </Button>
            ) : null}
            {canComplete ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onCompleteOpenChange(true)}
              >
                Complete implementation
              </Button>
            ) : null}
          </div>
        }
      >
        {showNextAction ? (
          <NextActionCard title="Record effectiveness verification" />
        ) : (
          <Text tone="muted">
            {canStart
              ? "Start implementation to begin tracking progress."
              : canProgress
                ? "Update progress or complete implementation from here."
                : "No implementation action is available in the current status."}
          </Text>
        )}
      </Panel>

      <ConfirmationDialog
        open={startOpen}
        onOpenChange={onStartOpenChange}
        title="Start implementation"
        description={`Start implementation of ${control.code}? This uses version ${control.version}.`}
        confirmLabel="Start implementation"
        loading={startLoading}
        onConfirm={() => {
          void onStart();
        }}
      />

      <RiskControlCommandDialog
        open={progressOpen}
        onOpenChange={onProgressOpenChange}
        title="Update progress"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Update progress"
        loading={progressLoading}
        onConfirm={progressForm.handleSubmit((values) => onProgress(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="progress-value" required>
              Progress (%)
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
            <Label htmlFor="progress-note">Progress note</Label>
            <TextArea
              id="progress-note"
              {...progressForm.register("summary")}
            />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Text variant="label">Milestones</Text>
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
              <Text tone="muted">No milestones recorded.</Text>
            )}
            <HelperText>
              Milestones are read-only here — update them from the
              implementation plan.
            </HelperText>
          </div>
        </div>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={completeOpen}
        onOpenChange={onCompleteOpenChange}
        title="Complete implementation"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Complete implementation"
        loading={completeLoading}
        onConfirm={completeForm.handleSubmit((values) => onComplete(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Text tone="secondary">
            Marking the control implemented sets progress to 100% and makes
            effectiveness verification the next expected action.
          </Text>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="complete-summary" required>
              Completion summary
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
                Evidence waiver reason
              </Label>
              <TextArea
                id="complete-evidence-waiver-reason"
                {...completeForm.register("evidenceWaiverReason")}
                invalid={Boolean(
                  completeForm.formState.errors.evidenceWaiverReason,
                )}
              />
              <HelperText>
                Add at least one evidence reference, or record why evidence
                is waived.
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
                  onCheckedChange={(checked) => field.onChange(checked === true)}
                  label="Allow incomplete milestones"
                />
              )}
            />
          ) : null}
        </div>
      </RiskControlCommandDialog>
    </>
  );
}
