"use client";

import { useQuery } from "@tanstack/react-query";
import { Controller, type UseFormReturn } from "react-hook-form";

import {
  DatePicker,
  FieldError,
  Form,
  FormRow,
  FormSection,
  Input,
  Label,
  Select,
  type SelectOption,
  TextArea,
  ValidationSummary,
} from "@/components";

import { listComplianceDocuments } from "@/features/compliance-documents/api/compliance-documents-api";
import { complianceDocumentKeys } from "@/features/compliance-documents/api/compliance-documents-query-keys";
import { ComplianceDocumentTagInput } from "@/features/compliance-documents/components/compliance-document-tag-input";
import type { ComplianceDocumentFormValues } from "@/features/compliance-documents/schemas/compliance-document-form-schema";
import type {
  ComplianceDocumentListParams,
  ComplianceDocumentStatus,
  DocumentTypeDto,
} from "@/features/compliance-documents/types/compliance-documents-dto";
import { useOrganization } from "@/hooks/auth";

const ORDER_TYPE_CODE = "order";

// Picker candidates: the backend only accepts an in-force edition
// (active or under_review) as either an approving order or a supersede
// target. Applied on both pickers to keep the UI in sync with that rule.
function isInForce<T extends { status: ComplianceDocumentStatus }>(
  item: T,
): boolean {
  return item.status === "active" || item.status === "under_review";
}

function typeOptions(types: DocumentTypeDto[]): SelectOption[] {
  return types.map((type) => ({
    value: type.id,
    label: `${type.title_ru} (${type.code})`,
  }));
}

function documentOptions(
  items: Array<{ id: string; code: string; title: string }>,
  currentValue: string,
): SelectOption[] {
  const options: SelectOption[] = items.map((item) => ({
    value: item.id,
    label: `${item.code} — ${item.title}`,
  }));
  if (currentValue && !options.some((o) => o.value === currentValue)) {
    // The linked document is outside the loaded candidate window (archived,
    // superseded, draft, or past the first page). Keep the id so the form
    // round-trips it, but show a readable label instead of the raw UUID.
    options.unshift({
      value: currentValue,
      label: "Текущий связанный документ (вне списка)",
    });
  }
  options.unshift({ value: "", label: "— Не выбрано —" });
  return options;
}

interface Props {
  form: UseFormReturn<ComplianceDocumentFormValues>;
  onSubmit: (values: ComplianceDocumentFormValues) => void;
  id?: string;
  types: DocumentTypeDto[];
  // In edit mode the document type stays fixed (backend's update does not
  // accept document_type_id anyway).
  typeLocked?: boolean;
}

export function ComplianceDocumentForm({
  form,
  onSubmit,
  id = "compliance-document-form",
  types,
  typeLocked = false,
}: Props) {
  const {
    register,
    control,
    watch,
    formState: { errors },
  } = form;
  const { organizationId } = useOrganization();

  const documentTypeId = watch("document_type_id");
  const activeType = types.find((t) => t.id === documentTypeId);

  const summaryErrors = Object.values(errors)
    .map((error) => error?.message)
    .filter((message): message is string => Boolean(message));

  const orderTypeIds = types
    .filter((t) => t.code === ORDER_TYPE_CODE)
    .map((t) => t.id);

  // Pickers: load candidate documents the backend would accept for
  // approved_by_document_id and supersedes_document_id.
  const approvedByEnabled =
    (activeType?.requires_approval_order ?? false) && orderTypeIds.length > 0;
  const approvedByParams: ComplianceDocumentListParams = {
    document_type_id: orderTypeIds,
    include_archived: false,
    limit: 50,
    offset: 0,
  };
  const approvedByQuery = useQuery({
    queryKey: complianceDocumentKeys.list(organizationId, approvedByParams),
    queryFn: ({ signal }) => listComplianceDocuments(approvedByParams, signal),
    enabled: approvedByEnabled && Boolean(organizationId),
  });
  const approvedByCandidates = (approvedByQuery.data?.items ?? []).filter(
    isInForce,
  );

  const supersedesEnabled =
    documentTypeId.length > 0 && Boolean(organizationId);
  const supersedesParams: ComplianceDocumentListParams = {
    document_type_id: documentTypeId ? [documentTypeId] : [],
    include_archived: false,
    limit: 50,
    offset: 0,
  };
  const supersedesQuery = useQuery({
    queryKey: complianceDocumentKeys.list(organizationId, supersedesParams),
    queryFn: ({ signal }) => listComplianceDocuments(supersedesParams, signal),
    enabled: supersedesEnabled,
  });
  const supersedesCandidates = (supersedesQuery.data?.items ?? []).filter(
    isInForce,
  );

  return (
    <Form form={form} onSubmit={onSubmit} id={id}>
      {summaryErrors.length > 0 ? (
        <ValidationSummary errors={summaryErrors} />
      ) : null}

      <FormSection title="Основные сведения">
        <FormRow>
          <Label htmlFor="cd-type" required>
            Тип документа
          </Label>
          <Controller
            control={control}
            name="document_type_id"
            render={({ field }) => (
              <Select
                id="cd-type"
                value={field.value}
                onValueChange={field.onChange}
                options={typeOptions(types)}
                disabled={typeLocked}
                invalid={Boolean(errors.document_type_id)}
                placeholder="Выберите тип"
              />
            )}
          />
          {errors.document_type_id?.message ? (
            <FieldError>{errors.document_type_id.message}</FieldError>
          ) : null}
        </FormRow>

        <FormRow>
          <Label htmlFor="cd-code" required>
            Код
          </Label>
          <Input
            id="cd-code"
            {...register("code")}
            invalid={Boolean(errors.code)}
            autoComplete="off"
            maxLength={64}
          />
          {errors.code?.message ? (
            <FieldError>{errors.code.message}</FieldError>
          ) : null}
        </FormRow>

        <FormRow>
          <Label htmlFor="cd-title" required>
            Название
          </Label>
          <Input
            id="cd-title"
            {...register("title")}
            invalid={Boolean(errors.title)}
          />
          {errors.title?.message ? (
            <FieldError>{errors.title.message}</FieldError>
          ) : null}
        </FormRow>

        {activeType && activeType.subject_kind !== "organization" ? (
          <FormRow>
            <Label htmlFor="cd-subject">
              {activeType.subject_kind === "employee"
                ? "Работник (UUID)"
                : "Актив (UUID)"}
            </Label>
            <Input
              id="cd-subject"
              {...register("subject_id")}
              invalid={Boolean(errors.subject_id)}
              placeholder="00000000-0000-0000-0000-000000000000"
              autoComplete="off"
            />
            {errors.subject_id?.message ? (
              <FieldError>{errors.subject_id.message}</FieldError>
            ) : null}
          </FormRow>
        ) : null}
      </FormSection>

      <FormSection title="Даты">
        <FormRow>
          <Label htmlFor="cd-issued">Дата издания</Label>
          <DatePicker id="cd-issued" {...register("issued_at")} />
        </FormRow>
        <FormRow>
          <Label htmlFor="cd-effective">Действует с</Label>
          <DatePicker id="cd-effective" {...register("effective_from")} />
        </FormRow>
        <FormRow>
          <Label htmlFor="cd-next-review">Следующий пересмотр</Label>
          <DatePicker id="cd-next-review" {...register("next_review_at")} />
        </FormRow>
      </FormSection>

      <FormSection title="Связи">
        {approvedByEnabled ? (
          <FormRow>
            <Label htmlFor="cd-approved-by">Утверждён приказом</Label>
            <Controller
              control={control}
              name="approved_by_document_id"
              render={({ field }) => (
                <Select
                  id="cd-approved-by"
                  value={field.value}
                  onValueChange={field.onChange}
                  options={documentOptions(approvedByCandidates, field.value)}
                  invalid={Boolean(errors.approved_by_document_id)}
                />
              )}
            />
            {errors.approved_by_document_id?.message ? (
              <FieldError>{errors.approved_by_document_id.message}</FieldError>
            ) : null}
          </FormRow>
        ) : null}

        <FormRow>
          <Label htmlFor="cd-supersedes">Замещает документ</Label>
          <Controller
            control={control}
            name="supersedes_document_id"
            render={({ field }) => (
              <Select
                id="cd-supersedes"
                value={field.value}
                onValueChange={field.onChange}
                options={documentOptions(supersedesCandidates, field.value)}
                disabled={!supersedesEnabled}
                invalid={Boolean(errors.supersedes_document_id)}
              />
            )}
          />
          {errors.supersedes_document_id?.message ? (
            <FieldError>{errors.supersedes_document_id.message}</FieldError>
          ) : null}
        </FormRow>
      </FormSection>

      <FormSection title="Область применения">
        <FormRow>
          <Label htmlFor="cd-positions">Должности</Label>
          <Controller
            control={control}
            name="positions"
            render={({ field }) => (
              <ComplianceDocumentTagInput
                id="cd-positions"
                values={field.value}
                onChange={field.onChange}
                placeholder="Добавьте должность и нажмите Enter"
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="cd-work-types">Виды работ</Label>
          <Controller
            control={control}
            name="work_types"
            render={({ field }) => (
              <ComplianceDocumentTagInput
                id="cd-work-types"
                values={field.value}
                onChange={field.onChange}
                placeholder="Добавьте вид работ и нажмите Enter"
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="cd-departments">Подразделения</Label>
          <Controller
            control={control}
            name="departments"
            render={({ field }) => (
              <ComplianceDocumentTagInput
                id="cd-departments"
                values={field.value}
                onChange={field.onChange}
                placeholder="Добавьте подразделение и нажмите Enter"
              />
            )}
          />
        </FormRow>
      </FormSection>

      <FormSection title="Заметки">
        <FormRow>
          <Label htmlFor="cd-notes">Заметки</Label>
          <TextArea
            id="cd-notes"
            rows={4}
            {...register("notes")}
            invalid={Boolean(errors.notes)}
          />
        </FormRow>
      </FormSection>
    </Form>
  );
}
