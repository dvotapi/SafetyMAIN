"use client";

import {
  Button,
  FilterBar,
  FilterChip,
  MultiSelect,
  Select,
} from "@/components";

import type {
  ComplianceDocumentStatus,
  DocumentSubjectKind,
  DocumentTypeDto,
  SafetyDomain,
} from "@/features/compliance-documents/types/compliance-documents-dto";
import {
  COMPLIANCE_DOCUMENT_STATUSES,
  DOCUMENT_SUBJECT_KINDS,
  SAFETY_DOMAINS,
} from "@/features/compliance-documents/types/compliance-documents-dto";
import {
  complianceDocumentStatusLabel,
  documentSubjectKindLabel,
  safetyDomainLabel,
} from "@/features/compliance-documents/utils/status";
import type { ComplianceDocumentRegistryUrlState } from "@/features/compliance-documents/utils/filters";
import {
  DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE,
  hasActiveComplianceDocumentRegistryFilters,
} from "@/features/compliance-documents/utils/filters";

export function ComplianceDocumentFilterBar({
  state,
  documentTypes,
  onChange,
}: {
  state: ComplianceDocumentRegistryUrlState;
  documentTypes: DocumentTypeDto[];
  onChange: (patch: Partial<ComplianceDocumentRegistryUrlState>) => void;
}) {
  const typeOptions = documentTypes.map((type) => ({
    value: type.id,
    label: type.title_ru,
  }));

  const typeTitleById = new Map(
    documentTypes.map((type) => [type.id, type.title_ru] as const),
  );

  return (
    <FilterBar>
      <Select
        aria-label="Фильтр по статусу"
        value={state.status || "__all"}
        onValueChange={(value) =>
          onChange({
            status:
              value === "__all" ? "" : (value as ComplianceDocumentStatus),
            page: 1,
          })
        }
        options={[
          { value: "__all", label: "Все статусы" },
          ...COMPLIANCE_DOCUMENT_STATUSES.map((status) => ({
            value: status,
            label: complianceDocumentStatusLabel(status),
          })),
        ]}
      />
      <Select
        aria-label="Фильтр по субъекту"
        value={state.subjectKind || "__all"}
        onValueChange={(value) =>
          onChange({
            subjectKind:
              value === "__all" ? "" : (value as DocumentSubjectKind),
            page: 1,
          })
        }
        options={[
          { value: "__all", label: "Любой субъект" },
          ...DOCUMENT_SUBJECT_KINDS.map((kind) => ({
            value: kind,
            label: documentSubjectKindLabel(kind),
          })),
        ]}
      />
      <Select
        aria-label="Фильтр по домену"
        value={state.safetyDomain || "__all"}
        onValueChange={(value) =>
          onChange({
            safetyDomain: value === "__all" ? "" : (value as SafetyDomain),
            page: 1,
          })
        }
        options={[
          { value: "__all", label: "Любой домен" },
          ...SAFETY_DOMAINS.map((domain) => ({
            value: domain,
            label: safetyDomainLabel(domain),
          })),
        ]}
      />
      <MultiSelect
        values={state.documentTypeIds}
        onValuesChange={(ids) => onChange({ documentTypeIds: ids, page: 1 })}
        options={typeOptions}
        placeholder="Тип документа"
      />
      <Button
        type="button"
        variant={state.reviewDueOnly ? "primary" : "secondary"}
        size="sm"
        onClick={() =>
          onChange({ reviewDueOnly: !state.reviewDueOnly, page: 1 })
        }
      >
        Нужен пересмотр
      </Button>
      <Button
        type="button"
        variant={state.includeArchived ? "primary" : "secondary"}
        size="sm"
        onClick={() =>
          onChange({ includeArchived: !state.includeArchived, page: 1 })
        }
      >
        Показать архив
      </Button>
      {state.status ? (
        <FilterChip
          label="Статус"
          value={complianceDocumentStatusLabel(state.status)}
          onRemove={() => onChange({ status: "", page: 1 })}
        />
      ) : null}
      {state.subjectKind ? (
        <FilterChip
          label="Субъект"
          value={documentSubjectKindLabel(state.subjectKind)}
          onRemove={() => onChange({ subjectKind: "", page: 1 })}
        />
      ) : null}
      {state.safetyDomain ? (
        <FilterChip
          label="Домен"
          value={safetyDomainLabel(state.safetyDomain)}
          onRemove={() => onChange({ safetyDomain: "", page: 1 })}
        />
      ) : null}
      {state.documentTypeIds.map((id) => (
        <FilterChip
          key={id}
          label="Тип"
          value={typeTitleById.get(id) ?? id}
          onRemove={() =>
            onChange({
              documentTypeIds: state.documentTypeIds.filter((v) => v !== id),
              page: 1,
            })
          }
        />
      ))}
      {state.reviewDueOnly ? (
        <FilterChip
          label="Пересмотр"
          value="Нужен пересмотр"
          onRemove={() => onChange({ reviewDueOnly: false, page: 1 })}
        />
      ) : null}
      {state.includeArchived ? (
        <FilterChip
          label="Архив"
          value="Включён"
          onRemove={() => onChange({ includeArchived: false, page: 1 })}
        />
      ) : null}
      {hasActiveComplianceDocumentRegistryFilters(state) ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() =>
            onChange({ ...DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE })
          }
        >
          Сбросить фильтры
        </Button>
      ) : null}
    </FilterBar>
  );
}
