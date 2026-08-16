import { z } from "zod";

import type { EvidenceRequestDto } from "@/features/risk-controls/types/risk-control-dto";

/**
 * `metadata` (a free-form string map on `EvidenceRequestDto`) has no product
 * requirement for this form and is intentionally left out of the UI — it is
 * never wired to a field here and is never sent by `evidenceFormValuesToRequest`.
 */
const baseEvidenceFormSchema = z.object({
  evidenceType: z.enum([
    "document",
    "photo",
    "video",
    "inspection_record",
    "test_result",
    "work_order",
    "training_record",
    "certificate",
    "measurement",
    "approval",
    "other",
  ]),
  externalReference: z.string().trim().min(1, "Укажите внешнюю ссылку"),
  title: z.string().trim().min(1, "Укажите название"),
  description: z.string().trim(),
  checksum: z.string().trim(),
  allowAfterImplemented: z.boolean(),
});

/**
 * `allowAfterImplemented` is required (must be checked) only when the
 * control is in a post-implementation status (`implemented` /
 * `verified_effective` / `verified_ineffective`). Without it the backend
 * would reject the request with 422 — this schema makes that impossible to
 * reach client-side by blocking submit until the checkbox is checked.
 */
export function buildEvidenceFormSchema(requireAllowAfterImplemented: boolean) {
  if (!requireAllowAfterImplemented) {
    return baseEvidenceFormSchema;
  }
  return baseEvidenceFormSchema.refine(
    (values) => values.allowAfterImplemented === true,
    {
      message: "Подтвердите добавление доказательства после внедрения",
      path: ["allowAfterImplemented"],
    },
  );
}

export const evidenceFormSchema = baseEvidenceFormSchema;

export type EvidenceFormValues = z.infer<typeof baseEvidenceFormSchema>;

export const DEFAULT_EVIDENCE_FORM_VALUES: EvidenceFormValues = {
  evidenceType: "document",
  externalReference: "",
  title: "",
  description: "",
  checksum: "",
  allowAfterImplemented: false,
};

/**
 * Builds the `add-evidence` request body from validated form values.
 * Mirrors the backend's `EvidenceRequest` — `POST .../evidence` expects
 * `{expected_version, evidence_type, external_reference, title, description?,
 * checksum?, allow_after_implemented?}`. `metadata` is never sent — see the
 * schema comment above.
 */
export function evidenceFormValuesToRequest(
  values: EvidenceFormValues,
  expectedVersion: number,
): EvidenceRequestDto {
  const description = values.description.trim();
  const checksum = values.checksum.trim();
  return {
    expected_version: expectedVersion,
    evidence_type: values.evidenceType,
    external_reference: values.externalReference.trim(),
    title: values.title.trim(),
    ...(description ? { description } : {}),
    ...(checksum ? { checksum } : {}),
    ...(values.allowAfterImplemented ? { allow_after_implemented: true } : {}),
  };
}
