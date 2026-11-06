/** Synthetic shelf payloads for tests (never real workbook data). */
import type {
  ShelfOverviewDto,
  ShelfSectionSlotsDto,
  ShelfSlotDetailDto,
  ShelfSlotSummaryDto,
} from "@/features/document-shelf/types/shelf-dto";

const counts = (
  over: Partial<ShelfOverviewDto["totals"]["by_group"]> = {},
) => ({
  present: 0,
  review: 0,
  in_progress: 0,
  missing: 0,
  to_clarify: 0,
  excluded: 0,
  ...over,
});

export function slotSummary(
  code: string,
  over: Partial<ShelfSlotSummaryDto> = {},
): ShelfSlotSummaryDto {
  const index = Number(code.slice(-2));
  return {
    id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`,
    code,
    subsection_code: code.split(".").slice(0, 2).join("."),
    short_title: `Место ${code}`,
    title: `Синтетическое место ${code}`,
    document_kind: "План",
    kept_on: "organization",
    obligation_level: "mandatory",
    effective_status: "missing",
    group: "missing",
    has_acknowledgement_gap: false,
    ...over,
  };
}

export function overviewFixture(): ShelfOverviewDto {
  return {
    sections: [
      {
        code: "ПожБ",
        number: 8,
        title: "Пожарная безопасность",
        safety_domain: "fire",
        total: 1,
        mandatory_total: 1,
        by_group: counts({ in_progress: 1 }),
        readiness_percent: 0,
        strip: [{ code: "ПожБ.01.01", group: "in_progress" }],
      },
      {
        code: "ТрБ",
        number: 10,
        title: "Транспортная безопасность",
        safety_domain: "transport_security",
        total: 4,
        mandatory_total: 3,
        by_group: counts({
          present: 1,
          missing: 1,
          to_clarify: 1,
          excluded: 1,
        }),
        readiness_percent: 50,
        strip: [
          { code: "ТрБ.01.01", group: "present" },
          { code: "ТрБ.01.02", group: "missing" },
          { code: "ТрБ.02.01", group: "to_clarify" },
          { code: "ТрБ.02.02", group: "excluded" },
        ],
      },
    ],
    totals: {
      places: 5,
      excluded: 1,
      by_group: counts({
        present: 1,
        in_progress: 1,
        missing: 1,
        to_clarify: 1,
        excluded: 1,
      }),
      readiness_percent: 40,
    },
    evaluated_at: "2026-11-05T09:00:00Z",
    last_imported_at: "2026-11-04T09:00:00Z",
  };
}

export function transportSectionFixture(): ShelfSectionSlotsDto {
  return {
    section: { code: "ТрБ", number: 10, title: "Транспортная безопасность" },
    subsections: [
      {
        code: "ТрБ.01",
        title: "Оценка уязвимости",
        slots: [
          slotSummary("ТрБ.01.01", {
            effective_status: "present",
            group: "present",
            document_kind: "Журнал",
          }),
          slotSummary("ТрБ.01.02"),
        ],
      },
      {
        code: "ТрБ.02",
        title: "План обеспечения",
        slots: [
          slotSummary("ТрБ.02.01", {
            effective_status: "to_clarify",
            group: "to_clarify",
            obligation_level: "conditional",
          }),
          slotSummary("ТрБ.02.02", {
            effective_status: "excluded",
            group: "excluded",
          }),
        ],
      },
    ],
  };
}

export function slotDetail(
  code: string,
  over: Partial<ShelfSlotDetailDto> = {},
): ShelfSlotDetailDto {
  return {
    ...slotSummary(code),
    section_code: code.split(".")[0]!,
    legal_basis: {
      regulation: "16-ФЗ",
      clause: "ст. 9",
      quote: "",
      source_url: "https://pravo.gov.ru/doc",
      confidence: "verified",
    },
    applicability_condition: "",
    review_cycle_text: "5 лет",
    review_period_months: 60,
    review_date: null,
    curated_status: "missing",
    document_type_code: "transport_plan",
    proposed_document_type: "",
    responsible_text: "",
    legacy_location: "",
    notes: "",
    package_code: "",
    legacy_code: "",
    exclusion: null,
    current_document: null,
    editions: [],
    available_actions: ["develop_document", "link_document", "exclude"],
    primary_action: "develop_document",
    acknowledgement: null,
    version: 3,
    ...over,
  };
}

export const DOCUMENT_ID = "11111111-2222-4333-8444-555555555555";
export const FILE_ID = "99999999-8888-4777-8666-555555555555";
