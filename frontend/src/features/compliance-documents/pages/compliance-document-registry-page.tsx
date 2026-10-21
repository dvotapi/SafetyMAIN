"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
  RegistryFooter,
  RegistryPagination,
  RegistryTable,
  RegistryToolbar,
  Search,
  StatusBadge,
  Text,
  type DataTableColumnDef,
} from "@/components";
import { PageContainer, PageHeader } from "@/components/patterns/Page";

import {
  useComplianceDocumentListQuery,
  useDocumentTypesQuery,
} from "@/features/compliance-documents/api/compliance-documents-queries";
import { ComplianceDocumentFilterBar } from "@/features/compliance-documents/components/compliance-document-filter-bar";
import { ComplianceDocumentStatusBadge } from "@/features/compliance-documents/components/compliance-document-status-badge";
import { mapComplianceDocumentCapabilities } from "@/features/compliance-documents/hooks/use-compliance-document-permissions";
import type { ComplianceDocument } from "@/features/compliance-documents/types/compliance-documents-dto";
import {
  DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE,
  hasActiveComplianceDocumentRegistryFilters,
  parseComplianceDocumentRegistrySearchParams,
  registryStateToListParams,
  serializeComplianceDocumentRegistrySearchParams,
  type ComplianceDocumentRegistryUrlState,
} from "@/features/compliance-documents/utils/filters";
import { shouldShowReviewDueWarning } from "@/features/compliance-documents/utils/status";
import { useAuth } from "@/hooks/auth";
import { toUserSafeMessage } from "@/services/api/errors";
import { formatDateOnly } from "@/utils/format-date";

export function ComplianceDocumentRegistryPage() {
  const { hasPermission } = useAuth();
  const capabilities = mapComplianceDocumentCapabilities(hasPermission);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const state = useMemo(
    () =>
      parseComplianceDocumentRegistrySearchParams(
        new URLSearchParams(searchParams.toString()),
      ),
    [searchParams],
  );
  const listParams = useMemo(() => registryStateToListParams(state), [state]);
  const query = useComplianceDocumentListQuery(
    listParams,
    capabilities.canRead,
  );
  const typesQuery = useDocumentTypesQuery({ enabled: capabilities.canRead });
  const [searchDraft, setSearchDraft] = useState(state.search);

  useEffect(() => {
    document.title = "Документы соответствия · SafetyMAIN";
  }, []);

  useEffect(() => {
    setSearchDraft(state.search);
  }, [state.search]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      if (searchDraft === state.search) return;
      updateState({ search: searchDraft, page: 1 });
    }, 300);
    return () => window.clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional debounce on draft
  }, [searchDraft]);

  function updateState(patch: Partial<ComplianceDocumentRegistryUrlState>) {
    const next = { ...state, ...patch };
    const params = serializeComplianceDocumentRegistrySearchParams(next);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  }

  const items = query.data?.items ?? [];
  const total = query.data?.pagination.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  const types = useMemo(() => typesQuery.data?.items ?? [], [typesQuery.data]);
  const typeTitleById = useMemo(() => {
    const map = new Map<string, string>();
    for (const type of types) map.set(type.id, type.title_ru);
    return map;
  }, [types]);

  useEffect(() => {
    if (query.data && state.page > totalPages && totalPages >= 1) {
      updateState({ page: totalPages });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- self-correct stale deep links only
  }, [state.page, totalPages, query.data]);

  const columns = useMemo<DataTableColumnDef<ComplianceDocument>[]>(
    () => [
      {
        id: "code",
        header: "Код",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/compliance-documents/${row.original.id}`}>
            {row.original.code}
          </Link>
        ),
      },
      {
        id: "title",
        header: "Название",
        enableSorting: false,
        cell: ({ row }) => row.original.title,
      },
      {
        id: "type",
        header: "Тип",
        enableSorting: false,
        cell: ({ row }) =>
          typeTitleById.get(row.original.document_type_id) ?? "—",
      },
      {
        id: "status",
        header: "Статус",
        enableSorting: false,
        cell: ({ row }) => (
          <ComplianceDocumentStatusBadge status={row.original.status} />
        ),
      },
      {
        id: "nextReview",
        header: "Следующий пересмотр",
        enableSorting: false,
        cell: ({ row }) => {
          const warn = shouldShowReviewDueWarning(
            row.original.status,
            row.original.is_review_due,
          );
          return (
            <div
              style={{
                display: "flex",
                gap: 8,
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <span>{formatDateOnly(row.original.next_review_at)}</span>
              {warn ? <StatusBadge status="overdue" label="Пересмотр" /> : null}
            </div>
          );
        },
      },
      {
        id: "updatedAt",
        header: "Обновлено",
        enableSorting: false,
        cell: ({ row }) => formatDateOnly(row.original.updated_at),
      },
    ],
    [typeTitleById],
  );

  if (!capabilities.canRead) {
    return (
      <PageContainer>
        <EmptyState
          title="Документы соответствия недоступны"
          description="Недостаточно прав для просмотра документов соответствия."
          action={
            <Button asChild variant="secondary">
              <Link href="/">Вернуться к обзору</Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  const filteredEmpty =
    !query.isLoading &&
    items.length === 0 &&
    hasActiveComplianceDocumentRegistryFilters(state);
  const empty =
    !query.isLoading &&
    items.length === 0 &&
    !hasActiveComplianceDocumentRegistryFilters(state);

  return (
    <PageContainer>
      <PageHeader
        title="Документы соответствия"
        description={
          <Text tone="secondary">
            Локальные акты, приказы, журналы и обучающие документы активной
            организации. Порядок задаёт сервер.
          </Text>
        }
      />

      <RegistryToolbar
        search={
          <Search
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Поиск по коду или названию"
            aria-label="Поиск документов соответствия"
          />
        }
        filters={
          <ComplianceDocumentFilterBar
            state={state}
            documentTypes={types}
            onChange={(patch) => updateState(patch)}
          />
        }
      />

      {!state.includeArchived ? (
        <Text tone="muted" variant="caption">
          Архивные документы по умолчанию скрыты.
        </Text>
      ) : null}

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Не удалось загрузить документы">
            {toUserSafeMessage(query.error)}
          </Alert>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void query.refetch()}
          >
            Повторить
          </Button>
        </div>
      ) : null}

      {query.isLoading && !query.data ? (
        <LoadingState label="Загрузка документов" />
      ) : empty ? (
        <EmptyState
          title="Документов пока нет"
          description="Создание документов станет доступно в следующем этапе."
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="Нет подходящих документов"
          description="Измените или сбросьте фильтры."
          action={
            <Button
              variant="secondary"
              onClick={() =>
                updateState({ ...DEFAULT_COMPLIANCE_DOCUMENT_REGISTRY_STATE })
              }
            >
              Сбросить фильтры
            </Button>
          }
        />
      ) : (
        <>
          <RegistryTable
            data={items}
            columns={columns}
            pageSize={state.pageSize}
            loading={query.isFetching && !query.isLoading}
            getRowId={(row) => row.id}
            emptyMessage="Документы не найдены"
          />
          <RegistryFooter
            pagination={
              <RegistryPagination
                summary={
                  <Text tone="muted" variant="caption">
                    Всего {total} · страница {state.page} из {totalPages}
                  </Text>
                }
              >
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={state.page <= 1}
                  onClick={() => updateState({ page: state.page - 1 })}
                >
                  Назад
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={state.page >= totalPages}
                  onClick={() => updateState({ page: state.page + 1 })}
                >
                  Вперёд
                </Button>
              </RegistryPagination>
            }
          />
        </>
      )}
    </PageContainer>
  );
}
