import type {
  AcceptanceDecisionDto,
  RiskAcceptance,
} from "@/features/risk-assessments/types/risk-assessment-types";

export type ApproveAcceptanceInput = {
  decision: AcceptanceDecisionDto;
  justification: string;
};

export type ApproveAcceptanceDraft = {
  decision: AcceptanceDecisionDto | "";
  justification: string;
};

export function prefillApproveAcceptance(
  acceptance: RiskAcceptance | null | undefined,
): ApproveAcceptanceDraft {
  return {
    decision: acceptance?.decision ?? "",
    justification: acceptance?.justification ?? "",
  };
}

/**
 * Client-side checks aligned with backend approve rules:
 * - decision required
 * - accepted / conditionally_accepted require justification
 */
export function validateApproveAcceptance(
  draft: ApproveAcceptanceDraft,
): string | null {
  if (!draft.decision) {
    return "Укажите решение о принятии";
  }
  if (
    (draft.decision === "accepted" ||
      draft.decision === "conditionally_accepted") &&
    draft.justification.trim().length === 0
  ) {
    return "Для принятого риска укажите обоснование";
  }
  return null;
}

export function toApproveAcceptanceInput(
  draft: ApproveAcceptanceDraft,
): ApproveAcceptanceInput | null {
  if (validateApproveAcceptance(draft) !== null || !draft.decision) {
    return null;
  }
  return {
    decision: draft.decision,
    justification: draft.justification.trim(),
  };
}
