import { z } from "zod";

/**
 * Zod response schemas mirror the backend's Pydantic contracts
 * (see backend/api/schemas/compliance_documents.py). They validate every
 * payload the compliance API returns so a backend/frontend contract drift
 * surfaces as a parse error here, not as a cryptic undefined later.
 *
 * Every object uses `.passthrough()` so a forward-compatible field the
 * backend adds reaches the parsed object instead of being silently
 * stripped. The TypeScript types stay sharp — reading an unknown field
 * still requires widening to `unknown` — but the raw value is present at
 * runtime for ad-hoc inspection and migration.
 */

export const complianceDocumentStatusSchema = z.enum([
  "draft",
  "approved",
  "active",
  "under_review",
  "superseded",
  "archived",
]);

export const complianceDocumentSourceSchema = z.enum([
  "manual",
  "generated",
  "hr_form",
]);

export const documentSubjectKindSchema = z.enum([
  "organization",
  "employee",
  "asset",
]);

export const safetyDomainSchema = z.enum([
  "occupational",
  "industrial",
  "labour",
  "fire",
  "environmental",
  "road",
  "dangerous_goods",
]);

export const documentApplicabilitySchema = z
  .object({
    positions: z.array(z.string()),
    work_types: z.array(z.string()),
    departments: z.array(z.string()),
    asset_ids: z.array(z.string().uuid()),
  })
  .passthrough();

export const documentFileSchema = z
  .object({
    id: z.string().uuid(),
    bucket: z.string(),
    key: z.string(),
    size_bytes: z.number().int().nonnegative(),
    content_type: z.string(),
    sha256: z.string(),
    original_filename: z.string(),
    uploaded_at: z.string(),
    uploaded_by: z.string().uuid(),
  })
  .passthrough();

export const documentTypeSchema = z
  .object({
    id: z.string().uuid(),
    organization_id: z.string().uuid(),
    code: z.string(),
    title_ru: z.string(),
    safety_domain: safetyDomainSchema,
    subject_kind: documentSubjectKindSchema,
    review_period_months: z.number().int().nullable(),
    validity_months: z.number().int().nullable(),
    periodicity_months: z.number().int().nullable(),
    warning_thresholds_days: z.array(z.number().int()),
    requires_acknowledgement: z.boolean(),
    requires_approval_order: z.boolean(),
    legal_basis: z.string(),
    legal_basis_reference: z.string().nullable(),
    is_active: z.boolean(),
    created_at: z.string(),
    updated_at: z.string(),
  })
  .passthrough();

export const documentTypeListSchema = z
  .object({
    items: z.array(documentTypeSchema),
  })
  .passthrough();

export const complianceDocumentSchema = z
  .object({
    id: z.string().uuid(),
    organization_id: z.string().uuid(),
    document_type_id: z.string().uuid(),
    subject_kind: documentSubjectKindSchema,
    subject_id: z.string().uuid().nullable(),
    code: z.string(),
    title: z.string(),
    status: complianceDocumentStatusSchema,
    issued_at: z.string().nullable(),
    effective_from: z.string().nullable(),
    next_review_at: z.string().nullable(),
    approved_by_document_id: z.string().uuid().nullable(),
    supersedes_document_id: z.string().uuid().nullable(),
    superseded_by_document_id: z.string().uuid().nullable(),
    applicability: documentApplicabilitySchema,
    source: complianceDocumentSourceSchema,
    current_file: documentFileSchema.nullable(),
    notes: z.string(),
    status_before_archive: complianceDocumentStatusSchema.nullable(),
    archive_reason: z.string().nullable(),
    is_review_due: z.boolean(),
    created_at: z.string(),
    created_by: z.string().uuid(),
    updated_at: z.string(),
    updated_by: z.string().uuid(),
    version: z.number().int().nonnegative(),
  })
  .passthrough();

export const paginationSchema = z
  .object({
    total: z.number().int().nonnegative(),
    offset: z.number().int().nonnegative(),
    limit: z.number().int().positive(),
  })
  .passthrough();

export const complianceDocumentListSchema = z
  .object({
    items: z.array(complianceDocumentSchema),
    pagination: paginationSchema,
  })
  .passthrough();

export const complianceDocumentDownloadUrlSchema = z
  .object({
    url: z.string().url(),
    expires_at: z.string(),
    filename: z.string(),
    content_type: z.string(),
    size_bytes: z.number().int().nonnegative(),
    sha256: z.string(),
  })
  .passthrough();

export const complianceDocumentFilesListSchema = z
  .object({
    items: z.array(documentFileSchema),
  })
  .passthrough();

export const complianceDocumentUploadUrlSchema = z.object({
  upload_id: z.string(),
  bucket: z.string(),
  key: z.string(),
  url: z.string().url(),
  method: z.string(),
  headers: z.record(z.string(), z.string()),
  expires_at: z.string(),
});

export type ComplianceDocumentDto = z.infer<typeof complianceDocumentSchema>;
export type ComplianceDocumentListDto = z.infer<
  typeof complianceDocumentListSchema
>;
export type DocumentTypeDto = z.infer<typeof documentTypeSchema>;
export type DocumentTypeListDto = z.infer<typeof documentTypeListSchema>;
export type DocumentFileDto = z.infer<typeof documentFileSchema>;
export type ComplianceDocumentDownloadUrlDto = z.infer<
  typeof complianceDocumentDownloadUrlSchema
>;
export type ComplianceDocumentFilesListDto = z.infer<
  typeof complianceDocumentFilesListSchema
>;
export type ComplianceDocumentUploadUrlDto = z.infer<
  typeof complianceDocumentUploadUrlSchema
>;
export type ComplianceDocumentStatus = z.infer<
  typeof complianceDocumentStatusSchema
>;
export type ComplianceDocumentSource = z.infer<
  typeof complianceDocumentSourceSchema
>;
export type DocumentSubjectKind = z.infer<typeof documentSubjectKindSchema>;
export type SafetyDomain = z.infer<typeof safetyDomainSchema>;
export type DocumentApplicability = z.infer<typeof documentApplicabilitySchema>;
export type PaginationDto = z.infer<typeof paginationSchema>;
