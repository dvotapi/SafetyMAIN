import { describe, expect, it } from "vitest";

import {
  latestVerification,
  mapOwnerDto,
  mapRiskControlDto,
  readWrappedId,
} from "@/features/risk-controls/mappers/risk-control-mappers";
import type { RiskControlDto } from "@/features/risk-controls/types/risk-control-dto";

const sampleDto: RiskControlDto = {
  id: "11111111-1111-1111-1111-111111111111",
  organization_id: "22222222-2222-2222-2222-222222222222",
  code: "RC-1",
  title: "Conveyor guard rail",
  description: "Fixed guard on the conveyor pinch point",
  hierarchy_level: "engineering",
  control_nature: "preventive",
  source: {
    source_type: "risk_assessment",
    source_reference: "RA-100",
    risk_assessment_id: { value: "33333333-3333-3333-3333-333333333333" },
    source_control_reference: "cm-1",
    assessment_version: 4,
    assessment_approved_at: "2026-07-01T00:00:00Z",
    residual_level: "medium",
    snapshot: { control_type: "engineering", description: "Install guard rail" },
  },
  hazard_id: "44444444-4444-4444-4444-444444444444",
  risk_assessment_id: "33333333-3333-3333-3333-333333333333",
  scope: [{ scope_type: "hazard", reference: "44444444-4444-4444-4444-444444444444" }],
  owner: {
    owner_type: "employee",
    owner_reference: "EMP-7",
    display_name_snapshot: "Maintenance Lead",
    assigned_at: "2026-07-02T00:00:00Z",
    assigned_by: "55555555-5555-5555-5555-555555555555",
  },
  implementation: {
    target_completion_date: "2026-09-01T00:00:00Z",
    progress: 40,
    summary: "Frame welded",
    milestones: [{ id: "m1", title: "Order steel", status: "completed" }],
  },
  evidence: [
    {
      id: "e1",
      evidence_type: "work_order",
      external_reference: "WO-9",
      title: "Fabrication order",
      captured_by: { value: "55555555-5555-5555-5555-555555555555" },
    },
  ],
  verifications: [
    {
      id: "v1",
      verification_type: "initial",
      method: "Inspection",
      result: "partially_effective",
      performed_by: { value: "55555555-5555-5555-5555-555555555555" },
    },
    {
      id: "v2",
      verification_type: "scheduled_review",
      method: "Audit",
      result: "effective",
      performed_by: { value: "55555555-5555-5555-5555-555555555555" },
    },
  ],
  review_schedule: {
    review_required: true,
    review_frequency_days: 365,
    next_review_date: "2027-07-01T00:00:00Z",
  },
  competency_requirements: [],
  related_entities: [],
  extension_data: {},
  lifecycle_status: "in_implementation",
  latest_effectiveness_result: "effective",
  next_review_date: "2027-07-01T00:00:00Z",
  is_overdue: false,
  verification_method_requirement: "Initial effectiveness verification",
  version: 5,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-10T00:00:00Z",
};

describe("readWrappedId", () => {
  it("unwraps {value} shape", () => {
    expect(readWrappedId({ value: "abc" })).toBe("abc");
  });
  it("passes flat strings through", () => {
    expect(readWrappedId("abc")).toBe("abc");
  });
  it("returns null for null and undefined", () => {
    expect(readWrappedId(null)).toBeNull();
    expect(readWrappedId(undefined)).toBeNull();
  });
});

describe("mapOwnerDto", () => {
  it("returns null when unassigned", () => {
    expect(mapOwnerDto(null)).toBeNull();
  });
  it("prefers the display name snapshot as label", () => {
    const owner = mapOwnerDto(sampleDto.owner);
    expect(owner?.label).toBe("Maintenance Lead");
    expect(owner?.assignedBy).toBe("55555555-5555-5555-5555-555555555555");
  });
  it("falls back to the reference when snapshot is blank", () => {
    const owner = mapOwnerDto({
      owner_type: "role",
      owner_reference: "ROLE-QA",
      display_name_snapshot: "   ",
      assigned_at: null,
      assigned_by: null,
    });
    expect(owner?.label).toBe("ROLE-QA");
  });
});

describe("mapRiskControlDto", () => {
  it("maps scalars and defaults", () => {
    const control = mapRiskControlDto(sampleDto);
    expect(control.code).toBe("RC-1");
    expect(control.status).toBe("in_implementation");
    expect(control.isOverdue).toBe(false);
    expect(control.version).toBe(5);
    expect(control.implementation.progress).toBe(40);
    expect(control.implementation.dependencies).toEqual([]);
    expect(control.implementation.milestones[0]?.title).toBe("Order steel");
  });

  it("unwraps nested id shapes", () => {
    const control = mapRiskControlDto(sampleDto);
    expect(control.source.riskAssessmentId).toBe(
      "33333333-3333-3333-3333-333333333333",
    );
    expect(control.evidence[0]?.capturedByUserId).toBe(
      "55555555-5555-5555-5555-555555555555",
    );
    expect(control.verifications[0]?.performedByUserId).toBe(
      "55555555-5555-5555-5555-555555555555",
    );
  });

  it("preserves the immutable source snapshot verbatim", () => {
    const control = mapRiskControlDto(sampleDto);
    expect(control.source.snapshot).toEqual({
      control_type: "engineering",
      description: "Install guard rail",
    });
  });

  it("keeps verification history in backend order", () => {
    const control = mapRiskControlDto(sampleDto);
    expect(control.verifications.map((v) => v.id)).toEqual(["v1", "v2"]);
    expect(latestVerification(control)?.id).toBe("v2");
  });

  it("tolerates absent optional blocks", () => {
    const control = mapRiskControlDto({
      ...sampleDto,
      owner: null,
      source: {},
      implementation: {},
      review_schedule: {},
      evidence: [],
      verifications: [],
      latest_effectiveness_result: null,
    });
    expect(control.owner).toBeNull();
    expect(control.implementation.progress).toBe(0);
    expect(control.reviewSchedule.reviewRequired).toBe(true);
    expect(latestVerification(control)).toBeNull();
  });
});
