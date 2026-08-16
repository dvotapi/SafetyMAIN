import type { VisualStatus } from "@/components";

import type {
  ControlNatureDto,
  ControlTypeDto,
  EffectivenessResultDto,
  EvidenceTypeDto,
  OwnerTypeDto,
  ReviewBasisDto,
  RiskControlStatusDto,
  VerifiableEffectivenessResultDto,
  VerificationTypeDto,
} from "@/features/risk-controls/types/risk-control-dto";

export const RISK_CONTROL_STATUSES: readonly RiskControlStatusDto[] = [
  "draft",
  "planned",
  "in_implementation",
  "implemented",
  "verified_effective",
  "verified_ineffective",
  "suspended",
  "superseded",
  "archived",
  "cancelled",
];

export const HIERARCHY_LEVELS: readonly ControlTypeDto[] = [
  "elimination",
  "substitution",
  "engineering",
  "administrative",
  "ppe",
];

export const CONTROL_NATURES: readonly ControlNatureDto[] = [
  "preventive",
  "detective",
  "mitigating",
  "recovery",
];

/** Only these three are accepted by the domain; the other two always 422. */
export const VERIFIABLE_RESULTS: readonly VerifiableEffectivenessResultDto[] = [
  "effective",
  "partially_effective",
  "ineffective",
];

export const EFFECTIVENESS_FILTER_VALUES: readonly EffectivenessResultDto[] = [
  "effective",
  "partially_effective",
  "ineffective",
  "not_verified",
  "not_applicable",
];

export const EVIDENCE_TYPES: readonly EvidenceTypeDto[] = [
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
];

export const VERIFICATION_TYPES: readonly VerificationTypeDto[] = [
  "initial",
  "scheduled_review",
  "post_incident",
  "post_inspection",
  "post_change",
  "management_review",
  "other",
];

export const REVIEW_BASES: readonly ReviewBasisDto[] = [
  "fixed_interval",
  "risk_based",
  "regulatory_requirement",
  "manufacturer_requirement",
  "corporate_policy",
  "post_incident",
  "post_change",
  "manual",
];

export const OWNER_TYPES: readonly OwnerTypeDto[] = [
  "user",
  "employee",
  "role",
  "organizational_unit",
  "external_party",
];

/**
 * Statuses in which a control is terminal-inactive — mirrors the domain's
 * `_TERMINAL_INACTIVE` set (backend/core/domain/entities/risk_control.py).
 * Single source of truth: import this instead of re-declaring the set.
 */
export const TERMINAL_INACTIVE_STATUSES: ReadonlySet<string> =
  new Set(["superseded", "archived", "cancelled"]);

/**
 * Statuses `record_verification` accepts — mirrors the domain's
 * `record_verification` guard. Single source of truth.
 */
export const VERIFY_ALLOWED_STATUSES: ReadonlySet<string> =
  new Set(["implemented", "verified_effective", "verified_ineffective"]);

/** `_TRANSITIONS["suspend"]` sources — every non-draft, non-terminal status. */
export const SUSPEND_ALLOWED_STATUSES: ReadonlySet<string> =
  new Set([
    "planned",
    "in_implementation",
    "implemented",
    "verified_effective",
    "verified_ineffective",
  ]);

/** `_TRANSITIONS["supersede"]` sources. */
export const SUPERSEDE_ALLOWED_STATUSES: ReadonlySet<string> =
  new Set([
    "implemented",
    "verified_effective",
    "verified_ineffective",
    "suspended",
  ]);

/** `_TRANSITIONS["cancel"]` sources. */
export const CANCEL_ALLOWED_STATUSES: ReadonlySet<string> =
  new Set(["draft", "planned", "in_implementation", "suspended"]);

/**
 * `_TRANSITIONS["archive"]` sources — notably not `planned` or
 * `in_implementation`, which must resolve (or be cancelled/suspended)
 * before they can be archived.
 */
export const ARCHIVE_ALLOWED_STATUSES: ReadonlySet<string> =
  new Set([
    "draft",
    "implemented",
    "verified_effective",
    "verified_ineffective",
    "suspended",
    "superseded",
    "cancelled",
  ]);

const STATUS_TO_VISUAL: Record<RiskControlStatusDto, VisualStatus> = {
  draft: "draft",
  planned: "planned",
  in_implementation: "in_implementation",
  implemented: "implemented",
  verified_effective: "verified_effective",
  verified_ineffective: "verified_ineffective",
  suspended: "suspended",
  superseded: "superseded",
  archived: "archived",
  cancelled: "cancelled",
};

const STATUS_LABELS: Record<RiskControlStatusDto, string> = {
  draft: "Draft",
  planned: "Planned",
  in_implementation: "In Implementation",
  implemented: "Implemented",
  verified_effective: "Verified Effective",
  verified_ineffective: "Verified Ineffective",
  suspended: "Suspended",
  superseded: "Superseded",
  archived: "Archived",
  cancelled: "Cancelled",
};

const EFFECTIVENESS_TO_VISUAL: Record<string, VisualStatus> = {
  effective: "verified_effective",
  partially_effective: "verified_partially_effective",
  ineffective: "verified_ineffective",
};

const EFFECTIVENESS_LABELS: Record<string, string> = {
  effective: "Verified Effective",
  partially_effective: "Verified Partially Effective",
  ineffective: "Verified Ineffective",
  not_verified: "Not verified",
  not_applicable: "Not applicable",
};

export function formatRiskControlEnumLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function riskControlStatusToVisual(
  status: RiskControlStatusDto,
): VisualStatus {
  return STATUS_TO_VISUAL[status];
}

export function riskControlStatusLabel(status: RiskControlStatusDto): string {
  return STATUS_LABELS[status];
}

/** Null when nothing has been verified yet — callers render text, not a badge. */
export function effectivenessToVisual(
  result: string | null | undefined,
): VisualStatus | null {
  if (!result) {
    return null;
  }
  return EFFECTIVENESS_TO_VISUAL[result] ?? null;
}

export function effectivenessLabel(result: string | null | undefined): string {
  if (!result) {
    return "Not verified";
  }
  return EFFECTIVENESS_LABELS[result] ?? formatRiskControlEnumLabel(result);
}

/** Implementation is a separate dimension from lifecycle status. */
export function implementationStateLabel(input: {
  status: RiskControlStatusDto;
  progress: number;
  actualCompletionDate: string | null;
}): string {
  if (input.actualCompletionDate) {
    return "Implemented";
  }
  switch (input.status) {
    case "draft":
      return "Not planned";
    case "planned":
      return "Planned";
    case "in_implementation":
      return `In progress — ${input.progress}%`;
    case "implemented":
    case "verified_effective":
    case "verified_ineffective":
      return "Implemented";
    default:
      return input.progress > 0
        ? `In progress — ${input.progress}%`
        : "Not started";
  }
}
