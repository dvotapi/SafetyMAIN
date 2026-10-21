import { describe, expect, it } from "vitest";

import {
  complianceDocumentToFormValues,
  formValuesToCreateRequest,
  formValuesToUpdateRequest,
} from "@/features/compliance-documents/mappers/compliance-document-form-mappers";
import type { ComplianceDocumentDto } from "@/features/compliance-documents/types/compliance-documents-dto";

const BASE_DOC: ComplianceDocumentDto = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  organization_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  document_type_id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
  subject_kind: "organization",
  subject_id: null,
  code: "CD-001",
  title: "Положение",
  status: "draft",
  issued_at: "2026-10-01",
  effective_from: "2026-10-02",
  next_review_at: "2029-10-01",
  approved_by_document_id: null,
  supersedes_document_id: null,
  superseded_by_document_id: null,
  applicability: {
    positions: ["Электрик"],
    work_types: ["Высота"],
    departments: ["Цех 1"],
    asset_ids: [
      "dddddddd-dddd-dddd-dddd-dddddddddddd",
      "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    ],
  },
  source: "manual",
  current_file: null,
  notes: "note",
  status_before_archive: null,
  archive_reason: null,
  is_review_due: false,
  created_at: "2026-10-01T00:00:00Z",
  created_by: "ffffffff-ffff-ffff-ffff-ffffffffffff",
  updated_at: "2026-10-01T00:00:00Z",
  updated_by: "ffffffff-ffff-ffff-ffff-ffffffffffff",
  version: 3,
};

describe("compliance document form mappers", () => {
  it("preserves applicability.asset_ids through edit round-trip", () => {
    const values = complianceDocumentToFormValues(BASE_DOC);
    expect(values.asset_ids).toEqual(BASE_DOC.applicability.asset_ids);

    const update = formValuesToUpdateRequest(values, BASE_DOC.version);
    expect(update.applicability?.asset_ids).toEqual(
      BASE_DOC.applicability.asset_ids,
    );
    expect(update.applicability?.positions).toEqual(["Электрик"]);
    expect(update.applicability?.work_types).toEqual(["Высота"]);
    expect(update.applicability?.departments).toEqual(["Цех 1"]);
    expect(update.expected_version).toBe(3);
  });

  it("creates request without empty optional fields and with trimmed strings", () => {
    const values = complianceDocumentToFormValues(BASE_DOC);
    const create = formValuesToCreateRequest({
      ...values,
      subject_id: "",
      issued_at: "",
      effective_from: "  2026-10-02  ",
    });
    expect(create.subject_id).toBeUndefined();
    expect(create.issued_at).toBeUndefined();
    expect(create.effective_from).toBe("2026-10-02");
    expect(create.applicability?.asset_ids).toEqual(
      BASE_DOC.applicability.asset_ids,
    );
    expect(create.source).toBe("manual");
  });

  it("sends null to clear previously-set optional dates on update", () => {
    const values = complianceDocumentToFormValues(BASE_DOC);
    const update = formValuesToUpdateRequest(
      {
        ...values,
        issued_at: "",
        effective_from: "",
        approved_by_document_id: "",
      },
      BASE_DOC.version,
    );
    expect(update.issued_at).toBeNull();
    expect(update.effective_from).toBeNull();
    expect(update.approved_by_document_id).toBeNull();
  });
});
