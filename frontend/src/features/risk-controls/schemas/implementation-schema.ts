import { z } from "zod";

import type { MilestoneStatusDto } from "@/features/risk-controls/types/risk-control-dto";
import type { PlanRiskControlDto } from "@/features/risk-controls/types/risk-control-dto";

export const MILESTONE_STATUS_VALUES: readonly MilestoneStatusDto[] = [
  "pending",
  "in_progress",
  "completed",
  "blocked",
  "cancelled",
];

const milestoneFormSchema = z.object({
  // A missing title makes the backend's implementation mapper raise
  // `KeyError` -> 500, so this is a hard client-side guarantee, not a
  // soft nicety.
  title: z.string().trim().min(1, "Milestone title is required"),
  description: z.string().trim(),
  dueDate: z.string().trim(),
  status: z.enum([
    "pending",
    "in_progress",
    "completed",
    "blocked",
    "cancelled",
  ]),
});

export type MilestoneFormValues = z.infer<typeof milestoneFormSchema>;

export const DEFAULT_MILESTONE: MilestoneFormValues = {
  title: "",
  description: "",
  dueDate: "",
  status: "pending",
};

/**
 * `verificationMethodRequirement` is required only when the control does
 * not already carry one — the backend rejects `plan` without it unless an
 * existing value covers the gap. Callers build the schema with the
 * control's current value so the conditional requirement matches the
 * control being planned.
 */
export function buildImplementationFormSchema(
  hasExistingVerificationMethodRequirement: boolean,
) {
  return z.object({
    targetStartDate: z.string().trim(),
    // Required — the backend rejects `plan` without a target completion date.
    targetCompletionDate: z
      .string()
      .trim()
      .min(1, "Target completion date is required"),
    implementationMethod: z.string().trim(),
    resourceNotes: z.string().trim(),
    dependencies: z.array(z.string().trim().min(1)),
    evidenceRequirements: z.array(z.string().trim().min(1)),
    verificationMethodRequirement: hasExistingVerificationMethodRequirement
      ? z.string().trim()
      : z
          .string()
          .trim()
          .min(1, "Verification method requirement is required"),
    milestones: z.array(milestoneFormSchema),
  });
}

export type ImplementationFormSchema = ReturnType<
  typeof buildImplementationFormSchema
>;
export type ImplementationFormValues = z.infer<ImplementationFormSchema>;

function toIsoDateOrNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? `${trimmed}T00:00:00Z` : null;
}

/**
 * Builds the `plan` request body from validated form values. Mirrors the
 * backend's `PlanRiskControlRequest` — `POST .../plan` expects
 * `{expected_version, implementation, verification_method_requirement}`.
 * Dates convert `YYYY-MM-DD` -> `${v}T00:00:00Z`; array position on
 * `milestones` is preserved as-is (no reordering is applied here).
 */
export function planFormValuesToRequest(
  values: ImplementationFormValues,
  expectedVersion: number,
): PlanRiskControlDto {
  const implementationMethod = values.implementationMethod.trim();
  const resourceNotes = values.resourceNotes.trim();
  const verificationMethodRequirement =
    values.verificationMethodRequirement.trim();

  return {
    expected_version: expectedVersion,
    implementation: {
      target_start_date: toIsoDateOrNull(values.targetStartDate),
      // Non-null: the schema guarantees a non-empty string here.
      target_completion_date: toIsoDateOrNull(values.targetCompletionDate),
      ...(implementationMethod
        ? { implementation_method: implementationMethod }
        : {}),
      ...(resourceNotes ? { resource_notes: resourceNotes } : {}),
      dependencies: values.dependencies,
      evidence_requirements: values.evidenceRequirements,
      milestones: values.milestones.map((milestone) => {
        const description = milestone.description.trim();
        return {
          title: milestone.title.trim(),
          ...(description ? { description } : {}),
          due_date: toIsoDateOrNull(milestone.dueDate),
          status: milestone.status,
        };
      }),
    },
    ...(verificationMethodRequirement
      ? { verification_method_requirement: verificationMethodRequirement }
      : {}),
  };
}
