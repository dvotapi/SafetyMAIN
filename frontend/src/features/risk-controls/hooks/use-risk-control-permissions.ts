import type { RiskControlCapabilities } from "@/features/risk-controls/types/risk-control-types";
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
