import { z } from "zod";

import type {
  ReasonVersionDto,
  SupersedeDto,
  SuspendDto,
} from "@/features/risk-controls/types/risk-control-dto";

/* ----------------------------------------------------------------------
 * Suspend
 * ---------------------------------------------------------------------- */

export const suspendFormSchema = z.object({
  reason: z.string().trim().min(1, "Reason is required"),
  expectedResolutionDate: z.string().trim(),
});

export type SuspendFormValues = z.infer<typeof suspendFormSchema>;

export const DEFAULT_SUSPEND_FORM_VALUES: SuspendFormValues = {
  reason: "",
  expectedResolutionDate: "",
};

export function suspendFormValuesToRequest(
  values: SuspendFormValues,
  expectedVersion: number,
): SuspendDto {
  return {
    expected_version: expectedVersion,
    reason: values.reason.trim(),
    expected_resolution_date: values.expectedResolutionDate.trim() || null,
  };
}

/* ----------------------------------------------------------------------
 * Supersede
 * ---------------------------------------------------------------------- */

/**
 * The backend does not validate that `replacement_control_id` refers to an
 * existing control — only that it is a UUID. Mirror that here: format
 * validation only, never a client-side existence check.
 */
export const supersedeFormSchema = z.object({
  replacementControlId: z
    .string()
    .trim()
    .min(1, "Replacement control ID is required")
    .uuid("Enter a valid UUID"),
  reason: z.string().trim().min(1, "Reason is required"),
});

export type SupersedeFormValues = z.infer<typeof supersedeFormSchema>;

export const DEFAULT_SUPERSEDE_FORM_VALUES: SupersedeFormValues = {
  replacementControlId: "",
  reason: "",
};

export function supersedeFormValuesToRequest(
  values: SupersedeFormValues,
  expectedVersion: number,
): SupersedeDto {
  return {
    expected_version: expectedVersion,
    replacement_control_id: values.replacementControlId.trim(),
    reason: values.reason.trim(),
  };
}

/* ----------------------------------------------------------------------
 * Cancel / archive — a version plus a mandatory reason (`ReasonVersionDto`)
 * ---------------------------------------------------------------------- */

export const reasonOnlyFormSchema = z.object({
  reason: z.string().trim().min(1, "Reason is required"),
});

export type ReasonOnlyFormValues = z.infer<typeof reasonOnlyFormSchema>;

export const DEFAULT_REASON_ONLY_FORM_VALUES: ReasonOnlyFormValues = {
  reason: "",
};

export function reasonOnlyFormValuesToRequest(
  values: ReasonOnlyFormValues,
  expectedVersion: number,
): ReasonVersionDto {
  return {
    expected_version: expectedVersion,
    reason: values.reason.trim(),
  };
}
