import { describe, expect, it } from "vitest";

import {
  shelfOverviewSchema,
  shelfSectionSlotsSchema,
  shelfSlotDetailSchema,
} from "@/features/document-shelf/schemas/shelf-response-schemas";
import {
  overviewFixture,
  slotSummary,
  transportSectionFixture,
} from "@/features/document-shelf/shelf-fixtures";
import {
  slotMatches,
  stripItemMatches,
} from "@/features/document-shelf/utils/shelf-filters";
import { pluralPlaces } from "@/features/document-shelf/utils/shelf-labels";
import {
  parseShelfUrlState,
  serializeShelfUrlState,
} from "@/features/document-shelf/utils/shelf-url-state";
import { spineSize } from "@/features/document-shelf/utils/spine-geometry";

describe("shelf schemas", () => {
  it("parse the overview and section payloads", () => {
    expect(shelfOverviewSchema.parse(overviewFixture()).sections).toHaveLength(
      2,
    );
    expect(
      shelfSectionSlotsSchema.parse(transportSectionFixture()).subsections,
    ).toHaveLength(2);
  });

  it("reject unknown statuses", () => {
    const bad = overviewFixture();
    (bad.sections[0]!.strip[0] as { group: string }).group = "lost";
    expect(() => shelfOverviewSchema.parse(bad)).toThrow();
  });

  it("parse a place detail", () => {
    const detail = shelfSlotDetailSchema.parse({
      ...slotSummary("ТрБ.01.01"),
      section_code: "ТрБ",
      legal_basis: {
        regulation: "16-ФЗ",
        clause: "",
        quote: "",
        source_url: null,
        confidence: "none",
      },
      applicability_condition: "",
      review_cycle_text: "",
      review_period_months: null,
      review_date: null,
      curated_status: "missing",
      document_type_code: null,
      proposed_document_type: "",
      responsible_text: "",
      legacy_location: "",
      notes: "",
      package_code: "",
      legacy_code: "",
      exclusion: null,
      current_document: null,
      editions: [],
      available_actions: ["develop_document", "upload_signed_scan", "exclude"],
      primary_action: "develop_document",
      acknowledgement: null,
      version: 1,
    });
    expect(detail.available_actions).toContain("upload_signed_scan");
  });
});

describe("URL state", () => {
  it("round-trips and drops invalid values", () => {
    const state = parseShelfUrlState(
      new URLSearchParams(
        "section=ТрБ&slot=ТрБ.02.02&filter=problems&excluded=hidden",
      ),
    );
    expect(state).toEqual({
      section: "ТрБ",
      slot: "ТрБ.02.02",
      filter: "problems",
      excludedHidden: true,
    });
    expect(
      parseShelfUrlState(new URLSearchParams(serializeShelfUrlState(state))),
    ).toEqual(state);
    expect(
      parseShelfUrlState(
        new URLSearchParams("section=Tr&slot=ТрБ.1.2&filter=x"),
      ),
    ).toEqual({
      section: null,
      slot: null,
      filter: "all",
      excludedHidden: false,
    });
    expect(
      parseShelfUrlState(new URLSearchParams("section=ТрБ&slot=ПожБ.01.01"))
        .slot,
    ).toBeNull();
    expect(
      serializeShelfUrlState(parseShelfUrlState(new URLSearchParams())),
    ).toBe("");
  });
});

describe("spine geometry (§4.3.5)", () => {
  it("looks sizes up by kind and obligation", () => {
    expect(spineSize("Журнал", "mandatory", false)).toEqual({
      width: 30,
      height: 136,
    });
    expect(spineSize("Приказ", "conditional", false)).toEqual({
      width: 22,
      height: 114,
    });
    expect(spineSize("Неизвестно", "recommended", false)).toEqual({
      width: 24,
      height: 98,
    });
    expect(spineSize("Журнал", "mandatory", true)).toEqual({
      width: 12,
      height: 70,
    });
  });
});

describe("filters (§4.3.1)", () => {
  it("dim by DTO fields only", () => {
    expect(slotMatches(slotSummary("ТрБ.01.01"), "problems")).toBe(true);
    expect(
      slotMatches(
        slotSummary("ТрБ.01.01", {
          group: "present",
          has_acknowledgement_gap: true,
        }),
        "problems",
      ),
    ).toBe(true);
    expect(
      slotMatches(
        slotSummary("ТрБ.01.01", { group: "to_clarify" }),
        "problems",
      ),
    ).toBe(false);
    expect(
      slotMatches(
        slotSummary("ТрБ.01.01", { obligation_level: "conditional" }),
        "mandatory",
      ),
    ).toBe(false);
    expect(
      slotMatches(slotSummary("ТрБ.01.01", { group: "excluded" }), "mandatory"),
    ).toBe(false);
    expect(stripItemMatches("review", "problems")).toBe(true);
    expect(stripItemMatches("present", "problems")).toBe(false);
  });

  it("pluralises places", () => {
    expect([1, 2, 5, 11, 21, 416].map(pluralPlaces)).toEqual([
      "место",
      "места",
      "мест",
      "мест",
      "место",
      "мест",
    ]);
  });
});
