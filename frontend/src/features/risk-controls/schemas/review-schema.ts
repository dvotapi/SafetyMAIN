import { z } from "zod";

import {
  DEFAULT_VERIFICATION_FORM_VALUES,
  buildVerificationFormSchema,
  verificationFormValuesToRequest,
  type VerificationFormValues,
} from "@/features/risk-controls/schemas/verification-schema";
import type {
  CompleteReviewDto,
  ScheduleReviewDto,
} from "@/features/risk-controls/types/risk-control-dto";

/* ----------------------------------------------------------------------
 * Schedule review
 * ---------------------------------------------------------------------- */

/**
 * Mirrors `ReviewBasisDto`/`REVIEW_BASES` in `utils/risk-control-status.ts`.
 * Kept as an explicit literal union here (not derived from the array), the
 * same pattern `verification-schema.ts` uses for `verificationType`.
 */
const reviewBasisEnum = z.enum([
  "fixed_interval",
  "risk_based",
  "regulatory_requirement",
  "manufacturer_requirement",
  "corporate_policy",
  "post_incident",
  "post_change",
  "manual",
]);

const reviewScheduleBaseSchema = z.object({
  reviewRequired: z.boolean(),
  reviewFrequencyDays: z
    .number({ invalid_type_error: "Review frequency is required" })
    .int("Review frequency must be a whole number")
    .min(1, "Review frequency must be at least 1 day")
    .nullable(),
  nextReviewDate: z.string().trim(),
  reviewBasis: reviewBasisEnum,
  escalationPolicyRef: z.string().trim(),
  noReviewReason: z.string().trim(),
});

export type ReviewScheduleFormValues = z.infer<
  typeof reviewScheduleBaseSchema
>;

export const DEFAULT_REVIEW_SCHEDULE_FORM_VALUES: ReviewScheduleFormValues = {
  reviewRequired: true,
  reviewFrequencyDays: null,
  nextReviewDate: "",
  reviewBasis: "fixed_interval",
  escalationPolicyRef: "",
  noReviewReason: "",
};

/**
 * Mirrors the domain rules enforced by `RiskControl.schedule_review`:
 * 1. When review is not required, a `noReviewReason` is mandatory.
 * 2. When review is required and no explicit `nextReviewDate` is given,
 *    `reviewFrequencyDays` is mandatory — the backend derives
 *    `now + frequency` when only the frequency is supplied.
 */
export const reviewScheduleFormSchema = reviewScheduleBaseSchema
  .refine((v) => v.reviewRequired || Boolean(v.noReviewReason), {
    path: ["noReviewReason"],
    message: "A no-review reason is required when review is not required.",
  })
  .refine(
    (v) =>
      !v.reviewRequired ||
      Boolean(v.nextReviewDate) ||
      v.reviewFrequencyDays !== null,
    {
      path: ["reviewFrequencyDays"],
      message:
        "Review frequency is required when no next review date is given.",
    },
  );

export type ReviewScheduleFormSchema = typeof reviewScheduleFormSchema;

function toIsoDateOrNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? `${trimmed}T00:00:00Z` : null;
}

/**
 * Builds the `schedule-review` request body from validated form values.
 * Mirrors the backend's `ScheduleReviewRequest`/`ReviewScheduleRequest` —
 * `POST .../schedule-review` expects `{expected_version, schedule: {...}}`.
 */
export function reviewScheduleFormValuesToRequest(
  values: ReviewScheduleFormValues,
  expectedVersion: number,
): ScheduleReviewDto {
  const escalationPolicyRef = values.escalationPolicyRef.trim();
  const noReviewReason = values.noReviewReason.trim();
  return {
    expected_version: expectedVersion,
    schedule: {
      review_required: values.reviewRequired,
      review_frequency_days: values.reviewRequired
        ? values.reviewFrequencyDays
        : null,
      next_review_date: toIsoDateOrNull(values.nextReviewDate),
      review_basis: values.reviewBasis,
      escalation_policy_ref: escalationPolicyRef || null,
      no_review_reason: values.reviewRequired ? null : noReviewReason,
    },
  };
}

/* ----------------------------------------------------------------------
 * Complete review — with an optional nested verification.
 * ---------------------------------------------------------------------- */

/**
 * The nested `verification` field is intentionally left unvalidated at this
 * level (`z.custom` pass-through) — its full field shape and cross-field
 * rules (the same ones `VerificationForm` enforces standalone) are applied
 * conditionally in `buildCompleteReviewFormSchema`'s `superRefine`, only
 * while `includeVerification` is checked. Validating it unconditionally
 * here would reject the untouched default values whenever the checkbox is
 * left off.
 */
const completeReviewBaseSchema = z.object({
  nextReviewDate: z.string().trim(),
  includeVerification: z.boolean(),
  verification: z.custom<VerificationFormValues>(() => true),
});

export type CompleteReviewFormValues = z.infer<
  typeof completeReviewBaseSchema
>;

export const DEFAULT_COMPLETE_REVIEW_FORM_VALUES: CompleteReviewFormValues = {
  nextReviewDate: "",
  includeVerification: false,
  verification: DEFAULT_VERIFICATION_FORM_VALUES,
};

/**
 * Builds the complete-review form schema. The nested `verification` object
 * is validated with the exact same cross-field rules as the standalone
 * record-verification form (`buildVerificationFormSchema`) — reused, not
 * re-implemented — but only while `includeVerification` is checked; an
 * unchecked verification is never validated (or sent).
 */
export function buildCompleteReviewFormSchema(options: {
  reviewRequired: boolean;
  noReviewReason: string | null;
  hasExistingEvidence: boolean;
}) {
  const verificationSchema = buildVerificationFormSchema(options);
  return completeReviewBaseSchema.superRefine((values, ctx) => {
    if (!values.includeVerification) {
      return;
    }
    const result = verificationSchema.safeParse(values.verification);
    if (!result.success) {
      for (const issue of result.error.issues) {
        ctx.addIssue({
          ...issue,
          path: ["verification", ...issue.path],
        });
      }
    }
  });
}

export type CompleteReviewFormSchema = ReturnType<
  typeof buildCompleteReviewFormSchema
>;

/**
 * Builds the `complete-review` request body from validated form values.
 * Mirrors the backend's `CompleteReviewRequest` — `POST .../complete-review`
 * expects `{expected_version, next_review_date?, verification?}`.
 *
 * TRAP 1 (nested `expected_version`): the nested `VerificationRequest`
 * inside `CompleteReviewRequest` still declares its own
 * `expected_version: int = Field(ge=1)`. The backend parses and validates
 * it (rejects anything < 1) but `complete_review`'s handler never reads it
 * — optimistic concurrency for this whole command is decided solely by the
 * top-level `expected_version`. We set the nested value to the control's
 * current version anyway, purely so the request is well-formed. Do not
 * "fix" this by deleting the field or by computing some other value for
 * it — it is validated-then-ignored by design, not a bug.
 *
 * TRAP 2 (double version bump): never derive the post-command version by
 * adding 1 to `expectedVersion` anywhere in the caller. When a
 * `verification` is included, `RiskControl.complete_review` bumps the
 * aggregate version twice server-side — once for completing the review,
 * once more when the verification is applied against the already-bumped
 * control — so the response version can be `expectedVersion + 2`, not
 * `+ 1`. Callers must always read `version` back from the mapped response
 * (`mapRiskControlDto(...).version`) and never compute it locally.
 */
export function completeReviewFormValuesToRequest(
  values: CompleteReviewFormValues,
  expectedVersion: number,
): CompleteReviewDto {
  const nextReviewDate = toIsoDateOrNull(values.nextReviewDate);
  return {
    expected_version: expectedVersion,
    ...(nextReviewDate ? { next_review_date: nextReviewDate } : {}),
    ...(values.includeVerification
      ? {
          verification: verificationFormValuesToRequest(
            values.verification,
            // Nested `expected_version` — validated then ignored, see the
            // TRAP 1 note above. Intentionally the same value as the
            // top-level `expected_version`, never `expectedVersion + 1`.
            expectedVersion,
          ),
        }
      : {}),
  };
}
