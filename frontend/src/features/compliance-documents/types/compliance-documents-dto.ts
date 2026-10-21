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
