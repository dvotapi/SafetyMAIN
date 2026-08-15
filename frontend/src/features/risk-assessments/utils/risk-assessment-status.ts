import type { VisualStatus } from "@/components";

import type {
  RiskAssessmentStatusDto,
  RiskLevelDto,
} from "@/features/risk-assessments/types/risk-assessment-types";

const STATUS_TO_VISUAL: Record<RiskAssessmentStatusDto, VisualStatus> = {
  draft: "draft",
  under_review: "under_review",
  approved: "approved",
  superseded: "superseded",
  archived: "archived",
};

const STATUS_LABELS: Record<RiskAssessmentStatusDto, string> = {
  draft: "Draft",
  under_review: "Under Review",
  approved: "Approved",
  superseded: "Superseded",
  archived: "Archived",
};

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  extreme: "Extreme",
};

export function riskAssessmentStatusToVisual(
  status: RiskAssessmentStatusDto,
): VisualStatus {
  return STATUS_TO_VISUAL[status];
}

export function riskAssessmentStatusLabel(
  status: RiskAssessmentStatusDto,
): string {
  return STATUS_LABELS[status];
}

export function riskLevelLabel(
  level: string | null | undefined,
): string | null {
  if (!level) {
    return null;
  }
  return RISK_LEVEL_LABELS[level] ?? formatRiskAssessmentEnumLabel(level);
}

export function formatRiskAssessmentEnumLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function isRiskLevelDto(value: string): value is RiskLevelDto {
  return (
    value === "low" ||
    value === "medium" ||
    value === "high" ||
    value === "extreme"
  );
}
