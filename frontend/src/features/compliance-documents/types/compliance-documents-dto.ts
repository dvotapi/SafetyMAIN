import type {
  ComplianceDocumentDto,
  ComplianceDocumentSource,
  ComplianceDocumentStatus,
  DocumentSubjectKind,
  SafetyDomain,
} from "@/features/compliance-documents/schemas/compliance-documents-response-schemas";

export type {
  ComplianceDocumentDto,
  ComplianceDocumentListDto,
  ComplianceDocumentDownloadUrlDto,
  ComplianceDocumentFilesListDto,
  ComplianceDocumentSource,
  ComplianceDocumentStatus,
  ComplianceDocumentUploadUrlDto,
  DocumentApplicability,
  DocumentFileDto,
  DocumentSubjectKind,
  DocumentTypeDto,
  DocumentTypeListDto,
  PaginationDto,
  SafetyDomain,
} from "@/features/compliance-documents/schemas/compliance-documents-response-schemas";

export type ComplianceDocument = ComplianceDocumentDto;

export interface ComplianceDocumentListParams {
  document_type_id?: string[];
  status?: ComplianceDocumentStatus;
  subject_kind?: DocumentSubjectKind;
  safety_domain?: SafetyDomain;
  review_due?: boolean;
  include_archived?: boolean;
  search?: string;
  offset?: number;
  limit?: number;
}

export interface VersionedRequestDto {
  expected_version: number;
}

export interface ReasonRequestDto extends VersionedRequestDto {
  reason: string;
}

export interface CompleteReviewRequestDto extends VersionedRequestDto {
  completed_on: string;
  next_review_at?: string | null;
}

export const DOCUMENT_SUBJECT_KINDS: readonly DocumentSubjectKind[] = [
  "organization",
  "employee",
  "asset",
];

export const SAFETY_DOMAINS: readonly SafetyDomain[] = [
  "occupational",
  "industrial",
  "labour",
  "fire",
  "environmental",
  "road",
  "dangerous_goods",
];

export const COMPLIANCE_DOCUMENT_STATUSES: readonly ComplianceDocumentStatus[] =
  ["draft", "approved", "active", "under_review", "superseded", "archived"];

export const COMPLIANCE_DOCUMENT_SOURCES: readonly ComplianceDocumentSource[] =
  ["manual", "generated", "hr_form"];

export interface DocumentApplicabilityPayload {
  positions: string[];
  work_types: string[];
  departments: string[];
  asset_ids: string[];
}

export interface CreateComplianceDocumentRequest {
  document_type_id: string;
  code: string;
  title: string;
  subject_id?: string | null;
  issued_at?: string | null;
  effective_from?: string | null;
  next_review_at?: string | null;
  approved_by_document_id?: string | null;
  supersedes_document_id?: string | null;
  applicability?: DocumentApplicabilityPayload;
  source?: ComplianceDocumentSource;
  notes?: string;
}

export interface UpdateComplianceDocumentRequest {
  expected_version: number;
  code?: string;
  title?: string;
  issued_at?: string | null;
  effective_from?: string | null;
  next_review_at?: string | null;
  approved_by_document_id?: string | null;
  supersedes_document_id?: string | null;
  applicability?: DocumentApplicabilityPayload;
  notes?: string | null;
}

export interface ComplianceDocumentUploadUrlRequest {
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
}

export interface ConfirmComplianceDocumentFileRequest {
  expected_version: number;
  key: string;
  size_bytes: number;
  sha256: string;
  content_type: string;
  original_filename: string;
}
