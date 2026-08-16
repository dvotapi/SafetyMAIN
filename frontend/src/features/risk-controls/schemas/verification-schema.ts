import { z } from "zod";

import type { VerificationRequestDto } from "@/features/risk-controls/types/risk-control-dto";

/**
 * `result` is a radio group over the three domain-accepted values only —
 * `not_verified` and `not_applicable` always 422 on the record-verification
 * endpoint, so they are never offered here (see `VERIFIABLE_RESULTS` in
 * `utils/risk-control-status.ts`). This is the single most compliance-
 * critical distinction in this feature: `partially_effective` must never be
 * collapsed into `effective` or `ineffective` anywhere in the UI.
 */
const baseVerificationFormSchema = z.object({
  verificationType: z.enum([
    "initial",
    "scheduled_review",
    "post_incident",
    "post_inspection",
    "post_change",
    "management_review",
    "other",
  ]),
  method: z.string().trim().min(1, "Method is required"),
  criteria: z.string().trim(),
  result: z.enum(["effective", "partially_effective", "ineffective"]),
  rating: z.string().trim(),
  findings: z.string().trim(),
  evidenceRefs: z.array(z.string().trim().min(1)),
  nextAction: z.string().trim(),
  nextReviewDate: z.string().trim(),
});

export type VerificationFormValues = z.infer<typeof baseVerificationFormSchema>;

export const DEFAULT_VERIFICATION_FORM_VALUES: VerificationFormValues = {
  verificationType: "initial",
  method: "",
  criteria: "",
  result: "effective",
  rating: "",
  findings: "",
  evidenceRefs: [],
  nextAction: "",
  nextReviewDate: "",
};

/**
 * Builds the record-verification form schema with two cross-field rules
 * matching the domain, both parameterized by the control being verified so
 * the client never blocks a submission the backend would accept, and never
 * lets through one the backend would 422:
 *
 * 1. When `result === "effective"`, a `nextReviewDate` is required unless
 *    the control's review schedule does not require review (`!reviewRequired`)
 *    or a `noReviewReason` is already on file.
 * 2. `evidenceRefs` may be submitted empty only if the control already has
 *    at least one evidence record (`hasExistingEvidence`).
 */
export function buildVerificationFormSchema(options: {
  reviewRequired: boolean;
  noReviewReason: string | null;
  hasExistingEvidence: boolean;
}) {
  const { reviewRequired, noReviewReason, hasExistingEvidence } = options;
  return baseVerificationFormSchema
    .refine(
      (v) =>
        v.result !== "effective" ||
        Boolean(v.nextReviewDate) ||
        !reviewRequired ||
        Boolean(noReviewReason),
      {
        path: ["nextReviewDate"],
        message:
          "A next review date is required when verifying a control effective.",
      },
    )
    .refine((v) => v.evidenceRefs.length > 0 || hasExistingEvidence, {
      path: ["evidenceRefs"],
      message: "At least one evidence reference is required.",
    });
}

export type VerificationFormSchema = ReturnType<
  typeof buildVerificationFormSchema
>;

function toIsoDateOrNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? `${trimmed}T00:00:00Z` : null;
}

/**
 * Builds the `record-verification` request body from validated form values.
 * Mirrors the backend's `VerificationRequest` — `POST .../verify` expects
 * `{expected_version, verification_type?, method, criteria?, result, rating?,
 * findings?, evidence_refs?, next_action?, next_review_date?, profile_key?,
 * profile_version?}`. `profile_key`/`profile_version` are sent explicitly as
 * the backend defaults (`"default"` / `"1"`) for clarity, not because the UI
 * offers a choice.
 */
export function verificationFormValuesToRequest(
  values: VerificationFormValues,
  expectedVersion: number,
): VerificationRequestDto {
  const criteria = values.criteria.trim();
  const rating = values.rating.trim();
  const findings = values.findings.trim();
  const nextAction = values.nextAction.trim();
  return {
    expected_version: expectedVersion,
    verification_type: values.verificationType,
    method: values.method.trim(),
    ...(criteria ? { criteria } : {}),
    result: values.result,
    ...(rating ? { rating } : {}),
    ...(findings ? { findings } : {}),
    evidence_refs: values.evidenceRefs,
    ...(nextAction ? { next_action: nextAction } : {}),
    next_review_date: toIsoDateOrNull(values.nextReviewDate),
    profile_key: "default",
    profile_version: "1",
  };
}
