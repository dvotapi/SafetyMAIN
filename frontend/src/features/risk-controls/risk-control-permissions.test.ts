import { describe, expect, it } from "vitest";

import { mapRiskControlCapabilities } from "@/features/risk-controls/hooks/use-risk-control-permissions";

const MEMBER_PERMISSIONS = [
  "risk_control:read",
  "risk_control:create",
  "risk_control:update",
  "risk_control:assign",
  "risk_control:implement",
  "risk_control:review",
  "risk_control:materialize",
];

function withPermissions(granted: string[]) {
  return (permission: string) => granted.includes(permission);
}

describe("mapRiskControlCapabilities", () => {
  it("grants everything to a full permission set", () => {
    const caps = mapRiskControlCapabilities(() => true);
    expect(Object.values(caps).every(Boolean)).toBe(true);
  });

  it("denies verify, suspend, supersede, archive and cancel to a member", () => {
    const caps = mapRiskControlCapabilities(withPermissions(MEMBER_PERMISSIONS));
    expect(caps.canRead).toBe(true);
    expect(caps.canImplement).toBe(true);
    expect(caps.canReview).toBe(true);
    expect(caps.canMaterialize).toBe(true);
    expect(caps.canVerify).toBe(false);
    expect(caps.canSuspend).toBe(false);
    expect(caps.canSupersede).toBe(false);
    expect(caps.canArchive).toBe(false);
    expect(caps.canCancel).toBe(false);
  });

  it("gives an auditor read plus activity only", () => {
    const caps = mapRiskControlCapabilities(
      withPermissions(["risk_control:read", "audit:read"]),
    );
    expect(caps.canRead).toBe(true);
    expect(caps.canViewActivity).toBe(true);
    expect(caps.canUpdate).toBe(false);
    expect(caps.canAssignOwner).toBe(false);
  });

  it("requires exact permission strings — no wildcard expansion", () => {
    const caps = mapRiskControlCapabilities(withPermissions(["risk_control:*"]));
    expect(caps.canRead).toBe(false);
  });

  it("gates related-object reads on their own feature permissions", () => {
    const caps = mapRiskControlCapabilities(
      withPermissions(["risk_control:read", "hazard:read"]),
    );
    expect(caps.canViewHazard).toBe(true);
    expect(caps.canViewAssessment).toBe(false);
  });
});
