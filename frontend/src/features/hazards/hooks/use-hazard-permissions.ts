import type {
  Hazard,
  HazardCapabilities,
  HazardLifecycleAction,
} from "@/features/hazards/types/hazard-types";
import { useAuth } from "@/hooks/auth";

export function mapHazardCapabilities(
  hasPermission: (permission: string) => boolean,
): HazardCapabilities {
  return {
    canRead: hasPermission("hazard:read"),
    canCreate: hasPermission("hazard:create"),
    canUpdate: hasPermission("hazard:update"),
    canActivate: hasPermission("hazard:activate"),
    canArchive: hasPermission("hazard:archive"),
    canRestore: hasPermission("hazard:restore"),
    canViewRelatedAssessments: hasPermission("risk:read"),
    canCreateRiskAssessment: hasPermission("risk:create"),
    canViewActivity: hasPermission("audit:read"),
  };
}

export function useHazardPermissions(): HazardCapabilities {
  const { hasPermission } = useAuth();
  return mapHazardCapabilities(hasPermission);
}

export function availableLifecycleActions(
  hazard: Pick<Hazard, "status">,
  capabilities: HazardCapabilities,
): HazardLifecycleAction[] {
  const actions: HazardLifecycleAction[] = [];
  if (hazard.status === "draft" && capabilities.canActivate) {
    actions.push("activate");
  }
  if (
    (hazard.status === "draft" || hazard.status === "active") &&
    capabilities.canArchive
  ) {
    actions.push("archive");
  }
  if (hazard.status === "archived" && capabilities.canRestore) {
    actions.push("restore");
  }
  return actions;
}

export function canEditHazardFields(
  hazard: Pick<Hazard, "status">,
  capabilities: HazardCapabilities,
): boolean {
  return capabilities.canUpdate && hazard.status !== "archived";
}

export function canEditHazardSource(
  hazard: Pick<Hazard, "status">,
  capabilities: HazardCapabilities,
): boolean {
  return canEditHazardFields(hazard, capabilities) && hazard.status === "draft";
}

/**
 * Product + backend rule: Risk Assessments may be created only for active
 * hazards (POST create requires an active hazard) and risk:create.
 */
export function canCreateRiskAssessmentForHazard(
  hazard: Pick<Hazard, "status">,
  capabilities: Pick<HazardCapabilities, "canCreateRiskAssessment">,
): boolean {
  return capabilities.canCreateRiskAssessment && hazard.status === "active";
}
