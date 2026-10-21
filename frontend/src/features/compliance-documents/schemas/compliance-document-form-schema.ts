import { z } from "zod";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const optionalIsoDate = z
  .string()
  .trim()
  .refine((value) => value.length === 0 || /^\d{4}-\d{2}-\d{2}$/u.test(value), {
    message: "Дата должна быть в формате ГГГГ-ММ-ДД",
  });

const optionalUuid = z
  .string()
  .trim()
  .refine((value) => value.length === 0 || UUID_RE.test(value), {
    message: "Некорректный идентификатор",
  });

const tagList = z.array(z.string().trim().min(1).max(255)).max(100);

export const complianceDocumentFormSchema = z.object({
  document_type_id: z
    .string()
    .trim()
    .min(1, "Выберите тип документа")
    .regex(UUID_RE, "Выберите тип документа"),
  code: z.string().trim().min(1, "Укажите код").max(64),
  title: z.string().trim().min(1, "Укажите название"),
  subject_id: optionalUuid,
  issued_at: optionalIsoDate,
  effective_from: optionalIsoDate,
  next_review_at: optionalIsoDate,
  approved_by_document_id: optionalUuid,
  supersedes_document_id: optionalUuid,
  positions: tagList,
  work_types: tagList,
  departments: tagList,
  notes: z.string().max(10_000),
});

export type ComplianceDocumentFormValues = z.infer<
  typeof complianceDocumentFormSchema
>;

export const defaultComplianceDocumentFormValues: ComplianceDocumentFormValues =
  {
    document_type_id: "",
    code: "",
    title: "",
    subject_id: "",
    issued_at: "",
    effective_from: "",
    next_review_at: "",
    approved_by_document_id: "",
    supersedes_document_id: "",
    positions: [],
    work_types: [],
    departments: [],
    notes: "",
  };
