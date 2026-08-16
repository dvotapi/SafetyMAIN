import { z } from "zod";

import type { AssignOwnerDto } from "@/features/risk-controls/types/risk-control-dto";

export const ownerFormSchema = z.object({
  ownerType: z.enum([
    "user",
    "employee",
    "role",
    "organizational_unit",
    "external_party",
  ]),
  ownerReference: z.string().trim().min(1, "Укажите ссылку на владельца"),
  displayName: z.string().trim().min(1, "Укажите отображаемое имя"),
  reason: z.string().trim(),
});

export type OwnerFormValues = z.infer<typeof ownerFormSchema>;

/**
 * Builds the `assign-owner` request body from validated form values.
 * Mirrors the backend's `AssignOwnerRequest`/`OwnerRequest` nesting —
 * `POST .../assign-owner` expects `{expected_version, owner, reason}`.
 */
export function ownerFormValuesToRequest(
  values: OwnerFormValues,
  expectedVersion: number,
): AssignOwnerDto {
  return {
    expected_version: expectedVersion,
    owner: {
      owner_type: values.ownerType,
      owner_reference: values.ownerReference.trim(),
      display_name_snapshot: values.displayName.trim(),
    },
    reason: values.reason.trim(),
  };
}
