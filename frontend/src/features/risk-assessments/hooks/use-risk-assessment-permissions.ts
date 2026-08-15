import type {
  RiskAssessment,
  RiskAssessmentCapabilities,
  RiskAssessmentLifecycleAction,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { useAuth } from "@/hooks/auth";

export function mapRiskAssessmentCapabilities(
  hasPermission: (permission: string) => boolean,
): RiskAssessmentCapabilities {
  return {
    canRead: hasPermission("risk:read"),
    canCreate: hasPermission("risk:create"),
    canUpdateDraft: hasPermission("risk:update"),
    /** Submit uses risk:update + submit_for_review — never invent risk:submit. */
    canSubmitForReview: hasPermission("risk:update"),
    canApprove: hasPermission("risk:approve"),
    canArchive: hasPermission("risk:archive"),
    canViewRelatedControls: hasPermission("risk_control:read"),
    canViewActivity: hasPermission("audit:read"),
  };
}

export function useRiskAssessmentPermissions(): RiskAssessmentCapabilities {
  const { hasPermission } = useAuth();
  return mapRiskAssessmentCapabilities(hasPermission);
}

/**
 * Product UX lifecycle gates. Approve is offered only for under_review
 * even though the backend domain may allow draft → approved.
 * Submit requires inherent risk (backend rejects otherwise).
 */
export function availableLifecycleActions(
  assessment: Pick<RiskAssessment, "status" | "inherentRisk">,
  capabilities: RiskAssessmentCapabilities,
): RiskAssessmentLifecycleAction[] {
  const actions: RiskAssessmentLifecycleAction[] = [];
  if (
    assessment.status === "draft" &&
    capabilities.canSubmitForReview &&
    assessment.inherentRisk !== null
  ) {
    actions.push("submit_for_review");
  }
  if (assessment.status === "under_review" && capabilities.canApprove) {
    actions.push("approve");
  }
  if (
    (assessment.status === "draft" ||
      assessment.status === "under_review" ||
      assessment.status === "approved" ||
      assessment.status === "superseded") &&
    capabilities.canArchive
  ) {
    actions.push("archive");
  }
  return actions;
}

export function canEditRiskAssessmentFields(
  assessment: Pick<RiskAssessment, "status">,
  capabilities: RiskAssessmentCapabilities,
): boolean {
  return capabilities.canUpdateDraft && assessment.status === "draft";
}
