import { describe, expect, it } from "vitest";

import {
  DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE,
  hasActiveComplianceDocumentRegistryFilters,
  parseComplianceDocumentRegistrySearchParams,
  registryStateToListParams,
  serializeComplianceDocumentRegistrySearchParams,
} from "@/features/compliance-documents/utils/filters";

describe("compliance document registry filters", () => {
  it("round-trips through URL search params", () => {
    const state = {
      ...DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE,
      search: "briefing",
      status: "active" as const,
      subjectKind: "employee" as const,
      safetyDomain: "fire" as const,
      documentTypeIds: ["11111111-1111-1111-1111-111111111111"],
      reviewDueOnly: true,
      includeArchived: true,
      page: 3,
    };
    const params = serializeComplianceDocumentRegistrySearchParams(state);
    const parsed = parseComplianceDocumentRegistrySearchParams(params);
    expect(parsed).toEqual(state);
  });

  it("drops invalid uuid and invalid status silently", () => {
    const params = new URLSearchParams();
    params.set("status", "not-a-status");
    params.append("documentTypeId", "not-a-uuid");
    params.append("documentTypeId", "22222222-2222-2222-2222-222222222222");
    const parsed = parseComplianceDocumentRegistrySearchParams(params);
    expect(parsed.status).toBe("");
    expect(parsed.documentTypeIds).toEqual([
      "22222222-2222-2222-2222-222222222222",
    ]);
  });

  it("has no active filters by default", () => {
    expect(
      hasActiveComplianceDocumentRegistryFilters(
        DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE,
      ),
    ).toBe(false);
  });

  it("translates state to API list params with offset derived from page", () => {
    const params = registryStateToListParams({
      ...DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE,
      page: 3,
      pageSize: 25,
      status: "draft",
      documentTypeIds: ["33333333-3333-3333-3333-333333333333"],
      reviewDueOnly: true,
    });
    expect(params.offset).toBe(50);
    expect(params.limit).toBe(25);
    expect(params.status).toBe("draft");
    expect(params.document_type_id).toEqual([
      "33333333-3333-3333-3333-333333333333",
    ]);
    expect(params.review_due).toBe(true);
  });
});
