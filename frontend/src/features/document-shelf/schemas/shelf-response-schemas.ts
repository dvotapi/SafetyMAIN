/**
 * Zod schemas of the shelf API (docs/api/ShelfAPI.md). Every value shown on the
 * shelf comes from these payloads; the frontend computes no status, count,
 * readiness or action (TASK-P11-012 §2.2).
 *
 * Objects use `.passthrough()` so a forward-compatible field the backend adds
 * later does not break parsing (same convention as compliance documents).
 */
import { z } from "zod";

export const SHELF_STATUS_GROUPS = [
  "present",
  "review",
  "in_progress",
  "missing",
  "to_clarify",
  "excluded",
] as const;

export const SHELF_EFFECTIVE_STATUSES = [
  "excluded",
  "present",
  "present_unverified",
  "review_due",
  "overdue_review",
  "under_review",
  "in_progress",
  "missing",
  "to_clarify",
] as const;

export const SHELF_ACTIONS = [
  "develop_document",
  "link_document",
  "exclude",
  "restore",
  "confirm_applicable",
  "open_project",
  "open_document",
  "upload_scan",
  "upload_signed_scan",
  "start_review",
  "send_for_acknowledgement",
] as const;

export const shelfStatusGroupSchema = z.enum(SHELF_STATUS_GROUPS);
export const shelfEffectiveStatusSchema = z.enum(SHELF_EFFECTIVE_STATUSES);
export const shelfActionSchema = z.enum(SHELF_ACTIONS);
export const slotKeptOnSchema = z.enum([
  "organization",
  "facility",
  "event",
  "employee",
  "asset",
  "profession",
]);
export const slotObligationLevelSchema = z.enum([
  "mandatory",
  "conditional",
  "recommended",
]);
export const curatedSlotStatusSchema = z.enum([
  "present",
  "present_needs_review",
  "in_progress",
  "missing",
  "to_clarify",
]);
export const slotExclusionReasonSchema = z.enum([
  "not_applicable",
  "condition_not_met",
  "duplicate",
  "other",
]);

export const shelfGroupCountsSchema = z
  .object({
    present: z.number().int().nonnegative(),
    review: z.number().int().nonnegative(),
    in_progress: z.number().int().nonnegative(),
    missing: z.number().int().nonnegative(),
    to_clarify: z.number().int().nonnegative(),
    excluded: z.number().int().nonnegative(),
  })
  .passthrough();

export const shelfSectionSummarySchema = z
  .object({
    code: z.string(),
    number: z.number().int(),
    title: z.string(),
    safety_domain: z.string(),
    total: z.number().int().nonnegative(),
    mandatory_total: z.number().int().nonnegative(),
    by_group: shelfGroupCountsSchema,
    readiness_percent: z.number().int().min(0).max(100),
    strip: z.array(
      z
        .object({ code: z.string(), group: shelfStatusGroupSchema })
        .passthrough(),
    ),
  })
  .passthrough();

export const shelfOverviewSchema = z
  .object({
    sections: z.array(shelfSectionSummarySchema),
    totals: z
      .object({
        places: z.number().int().nonnegative(),
        excluded: z.number().int().nonnegative(),
        by_group: shelfGroupCountsSchema,
        readiness_percent: z.number().int().min(0).max(100),
      })
      .passthrough(),
    evaluated_at: z.string(),
    last_imported_at: z.string().nullable(),
  })
  .passthrough();

export const shelfSlotSummarySchema = z
  .object({
    id: z.string().uuid(),
    code: z.string(),
    subsection_code: z.string(),
    short_title: z.string(),
    title: z.string(),
    document_kind: z.string(),
    kept_on: slotKeptOnSchema,
    obligation_level: slotObligationLevelSchema,
    effective_status: shelfEffectiveStatusSchema,
    group: shelfStatusGroupSchema,
    has_acknowledgement_gap: z.boolean(),
  })
  .passthrough();

export const shelfSlotListSchema = z
  .object({ items: z.array(shelfSlotSummarySchema) })
  .passthrough();

export const shelfSectionSlotsSchema = z
  .object({
    section: z
      .object({ code: z.string(), number: z.number().int(), title: z.string() })
      .passthrough(),
    subsections: z.array(
      z
        .object({
          code: z.string(),
          title: z.string(),
          slots: z.array(shelfSlotSummarySchema),
        })
        .passthrough(),
    ),
  })
  .passthrough();

const shelfDocumentFileSchema = z
  .object({
    file_id: z.string().uuid(),
    content_type: z.string(),
    size_bytes: z.number().int().nonnegative(),
    uploaded_at: z.string(),
  })
  .passthrough();

export const shelfSlotDetailSchema = shelfSlotSummarySchema
  .extend({
    section_code: z.string(),
    legal_basis: z
      .object({
        regulation: z.string(),
        clause: z.string(),
        quote: z.string(),
        source_url: z.string().nullable(),
        confidence: z.enum(["verified", "secondary", "unconfirmed", "none"]),
      })
      .passthrough(),
    applicability_condition: z.string(),
    review_cycle_text: z.string(),
    review_period_months: z.number().int().nullable(),
    review_date: z.string().nullable(),
    curated_status: curatedSlotStatusSchema,
    document_type_code: z.string().nullable(),
    proposed_document_type: z.string(),
    responsible_text: z.string(),
    legacy_location: z.string(),
    notes: z.string(),
    package_code: z.string(),
    legacy_code: z.string(),
    exclusion: z
      .object({
        reason: slotExclusionReasonSchema,
        comment: z.string(),
        excluded_by_name: z.string(),
        excluded_at: z.string(),
      })
      .passthrough()
      .nullable(),
    current_document: z
      .object({
        id: z.string().uuid(),
        code: z.string(),
        title: z.string(),
        status: z.string(),
        effective_from: z.string().nullable(),
        next_review_at: z.string().nullable(),
        approved_by_order: z
          .object({ code: z.string(), title: z.string() })
          .passthrough()
          .nullable(),
        signed_scan: shelfDocumentFileSchema.nullable(),
        working_file: shelfDocumentFileSchema.nullable(),
      })
      .passthrough()
      .nullable(),
    editions: z.array(
      z
        .object({
          id: z.string().uuid(),
          code: z.string(),
          status: z.string(),
          effective_from: z.string().nullable(),
        })
        .passthrough(),
    ),
    available_actions: z.array(shelfActionSchema),
    primary_action: shelfActionSchema.nullable(),
    acknowledgement: z.unknown().nullable(),
    version: z.number().int().positive(),
  })
  .passthrough();

export type ShelfStatusGroup = z.infer<typeof shelfStatusGroupSchema>;
export type ShelfEffectiveStatus = z.infer<typeof shelfEffectiveStatusSchema>;
export type ShelfAction = z.infer<typeof shelfActionSchema>;
export type ShelfGroupCountsDto = z.infer<typeof shelfGroupCountsSchema>;
export type ShelfSectionSummaryDto = z.infer<typeof shelfSectionSummarySchema>;
export type ShelfOverviewDto = z.infer<typeof shelfOverviewSchema>;
export type ShelfSlotSummaryDto = z.infer<typeof shelfSlotSummarySchema>;
export type ShelfSlotListDto = z.infer<typeof shelfSlotListSchema>;
export type ShelfSectionSlotsDto = z.infer<typeof shelfSectionSlotsSchema>;
export type ShelfSlotDetailDto = z.infer<typeof shelfSlotDetailSchema>;

export const developShelfSlotSchema = z
  .object({ document_id: z.string().uuid(), slot: shelfSlotDetailSchema })
  .passthrough();

/** Fields the shelf reads from compliance endpoints (only these are parsed). */
export const shelfDocumentRefSchema = z
  .object({
    id: z.string().uuid(),
    code: z.string(),
    title: z.string(),
    status: z.string(),
    version: z.number().int().positive(),
  })
  .passthrough();

export const shelfDocumentPageSchema = z
  .object({ items: z.array(shelfDocumentRefSchema) })
  .passthrough();

export const shelfFileUrlSchema = z
  .object({
    url: z.string(),
    filename: z.string(),
    content_type: z.string(),
  })
  .passthrough();

export const shelfDocumentTypesSchema = z
  .object({
    items: z.array(
      z
        .object({
          code: z.string(),
          title_ru: z.string(),
          subject_kind: z.string(),
          is_active: z.boolean(),
        })
        .passthrough(),
    ),
  })
  .passthrough();

export type DevelopShelfSlotDto = z.infer<typeof developShelfSlotSchema>;
export type ShelfDocumentRefDto = z.infer<typeof shelfDocumentRefSchema>;
export type ShelfFileUrlDto = z.infer<typeof shelfFileUrlSchema>;
export type ShelfDocumentTypesDto = z.infer<typeof shelfDocumentTypesSchema>;
export type SlotExclusionReason = z.infer<typeof slotExclusionReasonSchema>;
