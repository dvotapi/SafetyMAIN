import { describe, expect, it } from "vitest";

import { hazardKeys } from "@/features/hazards/api/hazard-query-keys";
import {
  availableLifecycleActions,
  canCreateRiskAssessmentForHazard,
  mapHazardCapabilities,
} from "@/features/hazards/hooks/use-hazard-permissions";
import {
  formValuesToCreateRequest,
  mapHazardDto,
} from "@/features/hazards/mappers/hazard-mappers";
import {
  defaultHazardFormValues,
  hazardFormSchema,
} from "@/features/hazards/schemas/hazard-form-schema";
import type { HazardDto } from "@/features/hazards/types/hazard-types";
import { hazardStatusToVisual } from "@/features/hazards/utils/hazard-status";
import {
  hasActiveRegistryFilters,
  parseRegistrySearchParams,
  registryStateToListParams,
  serializeRegistrySearchParams,
} from "@/features/hazards/utils/hazard-url-state";

const sampleDto: HazardDto = {
  id: "11111111-1111-1111-1111-111111111111",
  organization_id: "22222222-2222-2222-2222-222222222222",
  code: "HZ-1",
  title: "Unguarded machine",
  description: "Missing guard",
  category: "mechanical",
  safety_directions: ["occupational_safety"],
  source: "inspection",
  affected_subjects: ["employee"],
  location_reference: "Bay 3",
  process_reference: null,
  equipment_reference: null,
  extension_references: {},
  status: "draft",
  identified_at: "2026-07-25T00:00:00Z",
  identified_by: "33333333-3333-3333-3333-333333333333",
  reviewed_at: null,
  reviewed_by: null,
  archived_at: null,
  archived_by: null,
  created_at: "2026-07-25T00:00:00Z",
  updated_at: "2026-07-25T00:00:00Z",
  version: 1,
};

describe("hazard mappers", () => {
  it("maps dto to view model", () => {
    const hazard = mapHazardDto(sampleDto);
    expect(hazard.code).toBe("HZ-1");
    expect(hazard.organizationId).toBe(sampleDto.organization_id);
    expect(hazard.safetyDirections).toEqual(["occupational_safety"]);
  });

  it("maps form values to create request", () => {
    const body = formValuesToCreateRequest({
      ...defaultHazardFormValues,
      code: " HZ-2 ",
      title: " Title ",
      description: "",
      locationReference: "  ",
    });
    expect(body.code).toBe("HZ-2");
    expect(body.title).toBe("Title");
    expect(body.description).toBeUndefined();
    expect(body.location_reference).toBeUndefined();
  });
});

describe("hazard status", () => {
  it("maps to visual status", () => {
    expect(hazardStatusToVisual("draft")).toBe("draft");
    expect(hazardStatusToVisual("active")).toBe("active");
    expect(hazardStatusToVisual("archived")).toBe("archived");
  });
});

describe("hazard permissions", () => {
  it("maps capabilities from permissions", () => {
    const caps = mapHazardCapabilities((p) => p === "hazard:read");
    expect(caps.canRead).toBe(true);
    expect(caps.canCreate).toBe(false);
    expect(caps.canCreateRiskAssessment).toBe(false);
  });

  it("lists lifecycle actions by status", () => {
    const admin = mapHazardCapabilities(() => true);
    expect(availableLifecycleActions({ status: "draft" }, admin)).toEqual([
      "activate",
      "archive",
    ]);
    expect(availableLifecycleActions({ status: "archived" }, admin)).toEqual([
      "restore",
    ]);
  });

  it("allows Create Risk Assessment only for active hazards with risk:create", () => {
    const withCreate = mapHazardCapabilities((p) => p === "risk:create");
    const withoutCreate = mapHazardCapabilities(() => false);
    expect(
      canCreateRiskAssessmentForHazard({ status: "active" }, withCreate),
    ).toBe(true);
    expect(
      canCreateRiskAssessmentForHazard({ status: "draft" }, withCreate),
    ).toBe(false);
    expect(
      canCreateRiskAssessmentForHazard({ status: "archived" }, withCreate),
    ).toBe(false);
    expect(
      canCreateRiskAssessmentForHazard({ status: "active" }, withoutCreate),
    ).toBe(false);
  });
});

describe("hazard query keys", () => {
  it("scopes by organization", () => {
    expect(hazardKeys.detail("org-a", "h1")).not.toEqual(
      hazardKeys.detail("org-b", "h1"),
    );
  });
});

describe("registry url state", () => {
  it("parses and serializes", () => {
    const state = parseRegistrySearchParams(
      new URLSearchParams("search=chem&status=active&page=2"),
    );
    expect(state.search).toBe("chem");
    expect(state.status).toBe("active");
    expect(state.page).toBe(2);
    expect(hasActiveRegistryFilters(state)).toBe(true);
    const params = serializeRegistrySearchParams(state);
    expect(params.get("search")).toBe("chem");
    expect(registryStateToListParams(state).offset).toBe(25);
  });

  it("ignores invalid enums", () => {
    const state = parseRegistrySearchParams(
      new URLSearchParams("status=nope&category=bad"),
    );
    expect(state.status).toBe("");
    expect(state.category).toBe("");
  });
});

describe("hazard form schema", () => {
  it("requires safety directions", () => {
    const result = hazardFormSchema.safeParse({
      ...defaultHazardFormValues,
      safetyDirections: [],
    });
    expect(result.success).toBe(false);
  });
});
