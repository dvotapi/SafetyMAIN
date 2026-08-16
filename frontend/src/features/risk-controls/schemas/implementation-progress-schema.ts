import { z } from "zod";

import type {
  CompleteImplementationDto,
  ProgressDto,
} from "@/features/risk-controls/types/risk-control-dto";

export const progressFormSchema = z.object({
  progress: z
    .number({ invalid_type_error: "Progress is required" })
    .int("Progress must be a whole number")
    .min(0, "Progress must be between 0 and 100")
    .max(100, "Progress must be between 0 and 100"),
  summary: z.string().trim(),
});

export type ProgressFormValues = z.infer<typeof progressFormSchema>;

export const DEFAULT_PROGRESS_FORM_VALUES: ProgressFormValues = {
  progress: 0,
  summary: "",
};

/**
 * Builds the `update-progress` request body from validated form values.
 * Mirrors the backend's `ProgressRequest` — `POST .../progress` expects
 * `{expected_version, progress, summary}`. Milestones are intentionally
 * never sent here: the router accepts a `milestones` field on the
 * implementation DTO but never reads it from this endpoint.
 */
export function progressFormValuesToRequest(
  values: ProgressFormValues,
  expectedVersion: number,
): ProgressDto {
  const summary = values.summary.trim();
  return {
    expected_version: expectedVersion,
    progress: values.progress,
    ...(summary ? { summary } : {}),
  };
}

/**
 * `evidenceWaiverReason` is required only when the control currently has
 * no evidence attached — the backend rejects `complete_implementation`
 * without it in that case. Callers build the schema with
 * `control.evidence.length === 0` so the conditional requirement matches
 * the control being completed.
 */
export function buildCompleteImplementationFormSchema(
  evidenceIsEmpty: boolean,
) {
  return z.object({
    summary: z.string().trim().min(1, "Completion summary is required"),
    evidenceWaiverReason: evidenceIsEmpty
      ? z.string().trim().min(1, "Evidence waiver reason is required")
      : z.string().trim(),
    allowIncompleteMilestones: z.boolean(),
  });
}

export type CompleteImplementationFormSchema = ReturnType<
  typeof buildCompleteImplementationFormSchema
>;
export type CompleteImplementationFormValues =
  z.infer<CompleteImplementationFormSchema>;

export const DEFAULT_COMPLETE_IMPLEMENTATION_FORM_VALUES: CompleteImplementationFormValues =
  {
    summary: "",
    evidenceWaiverReason: "",
    allowIncompleteMilestones: false,
  };

/**
 * Builds the `complete-implementation` request body from validated form
 * values. Mirrors the backend's `CompleteImplementationRequest` —
 * `POST .../complete` expects
 * `{expected_version, summary, evidence_waiver_reason?, allow_incomplete_milestones?}`.
 */
export function completeImplementationFormValuesToRequest(
  values: CompleteImplementationFormValues,
  expectedVersion: number,
  evidenceIsEmpty: boolean,
): CompleteImplementationDto {
  const summary = values.summary.trim();
  const evidenceWaiverReason = values.evidenceWaiverReason.trim();
  return {
    expected_version: expectedVersion,
    summary,
    ...(evidenceIsEmpty
      ? { evidence_waiver_reason: evidenceWaiverReason }
      : {}),
    ...(values.allowIncompleteMilestones
      ? { allow_incomplete_milestones: true }
      : {}),
  };
}
