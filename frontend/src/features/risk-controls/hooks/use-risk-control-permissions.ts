import type {
  RiskControl,
  RiskControlCapabilities,
  RiskControlLifecycleAction,
} from "@/features/risk-controls/types/risk-control-types";
import {
  ARCHIVE_ALLOWED_STATUSES,
  CANCEL_ALLOWED_STATUSES,
  SUPERSEDE_ALLOWED_STATUSES,
  SUSPEND_ALLOWED_STATUSES,
  TERMINAL_INACTIVE_STATUSES,
  VERIFY_ALLOWED_STATUSES,
} from "@/features/risk-controls/utils/risk-control-status";
import { useAuth } from "@/hooks/auth";

/**
 * Frontend capabilities drive UX only; backend authorization stays
 * authoritative. Permission strings are matched exactly — the session
 * membership carries the expanded list, there is no wildcard.
 */
export function mapRiskControlCapabilities(
  hasPermission: (permission: string) => boolean,
): RiskControlCapabilities {
  return {
    canRead: hasPermission("risk_control:read"),
    canCreate: hasPermission("risk_control:create"),
    canUpdate: hasPermission("risk_control:update"),
    canAssignOwner: hasPermission("risk_control:assign"),
    canImplement: hasPermission("risk_control:implement"),
    canVerify: hasPermission("risk_control:verify"),
    canReview: hasPermission("risk_control:review"),
    /** Backend guards suspend and resume with the same permission. */
    canSuspend: hasPermission("risk_control:suspend"),
    canSupersede: hasPermission("risk_control:supersede"),
    canArchive: hasPermission("risk_control:archive"),
    canCancel: hasPermission("risk_control:cancel"),
    canMaterialize: hasPermission("risk_control:materialize"),
    canViewHazard: hasPermission("hazard:read"),
    canViewAssessment: hasPermission("risk:read"),
    canViewActivity: hasPermission("audit:read"),
  };
}

export function useRiskControlPermissions(): RiskControlCapabilities {
  const { hasPermission } = useAuth();
  return mapRiskControlCapabilities(hasPermission);
}

/**
 * Encodes the backend's `_TRANSITIONS` lifecycle table as UI action
 * availability. Each entry is gated on both the legal transition (per the
 * backend contract) and the matching capability — never one alone. Never
 * offers a delete action of any kind, for any status.
 *
 * Ordering: the forward/primary action for the current state first
 * (`plan` → `start_implementation` → `complete_implementation` → `verify`
 * → `schedule_review`), then the terminal commands
 * (`suspend`, `resume`, `supersede`, `cancel`, `archive`) last.
 */
export function availableLifecycleActions(
  control: Pick<RiskControl, "status" | "owner">,
  capabilities: RiskControlCapabilities,
): RiskControlLifecycleAction[] {
  const { status, owner } = control;
  const actions: RiskControlLifecycleAction[] = [];

  if (status === "draft" && owner !== null && capabilities.canUpdate) {
    actions.push("plan");
  }
  if (status === "planned" && capabilities.canImplement) {
    actions.push("start_implementation");
  }
  if (status === "in_implementation" && capabilities.canImplement) {
    actions.push("complete_implementation");
  }
  if (VERIFY_ALLOWED_STATUSES.has(status) && capabilities.canVerify) {
    actions.push("verify");
  }
  if (!TERMINAL_INACTIVE_STATUSES.has(status) && capabilities.canReview) {
    actions.push("schedule_review");
  }

  if (SUSPEND_ALLOWED_STATUSES.has(status) && capabilities.canSuspend) {
    actions.push("suspend");
  }
  /** Backend guards suspend and resume with the same permission. */
  if (status === "suspended" && capabilities.canSuspend) {
    actions.push("resume");
  }
  if (SUPERSEDE_ALLOWED_STATUSES.has(status) && capabilities.canSupersede) {
    actions.push("supersede");
  }
  if (CANCEL_ALLOWED_STATUSES.has(status) && capabilities.canCancel) {
    actions.push("cancel");
  }
  if (ARCHIVE_ALLOWED_STATUSES.has(status) && capabilities.canArchive) {
    actions.push("archive");
  }

  return actions;
}
