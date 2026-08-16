"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  Alert,
  Button,
  EmptyState,
  FilterBar,
  FilterChip,
  LoadingState,
  RegistryFooter,
  RegistryPagination,
  RegistryTable,
  RegistryToolbar,
  Search,
  Select,
  StatusBadge,
  Text,
  type DataTableColumnDef,
} from "@/components";
import { PageContainer, PageHeader } from "@/components/patterns/Page";
import { useHazardListQuery } from "@/features/hazards/api/hazard-queries";
import { mapHazardCapabilities } from "@/features/hazards/hooks/use-hazard-permissions";
import {
  HAZARD_CATEGORIES,
  HAZARD_SOURCES,
} from "@/features/hazards/schemas/hazard-form-schema";
import type { Hazard } from "@/features/hazards/types/hazard-types";
import {
  hazardCategoryLabel,
  hazardSourceLabel,
  hazardStatusLabel,
  hazardStatusToVisual,
} from "@/features/hazards/utils/hazard-status";
import {
  DEFAULT_REGISTRY_STATE,
  hasActiveRegistryFilters,
  parseRegistrySearchParams,
  registryStateToListParams,
  serializeRegistrySearchParams,
  type HazardRegistryUrlState,
} from "@/features/hazards/utils/hazard-url-state";
import { useAuth } from "@/hooks/auth";
import { toUserSafeMessage } from "@/services/api/errors";
import { APP_LOCALE } from "@/utils/locale";

function formatDate(value: string): string {
  try {
    return new Intl.DateTimeFormat(APP_LOCALE, {
      dateStyle: "medium",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function HazardRegistryPage() {
  const { hasPermission } = useAuth();
  const capabilities = mapHazardCapabilities(hasPermission);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const state = useMemo(
    () =>
      parseRegistrySearchParams(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );
  const listParams = useMemo(() => registryStateToListParams(state), [state]);
  const query = useHazardListQuery(listParams, capabilities.canRead);
  const [searchDraft, setSearchDraft] = useState(state.search);

  useEffect(() => {
    document.title = "Опасности · SafetyMAIN";
  }, []);

  useEffect(() => {
    setSearchDraft(state.search);
  }, [state.search]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      if (searchDraft === state.search) {
        return;
      }
      updateState({ search: searchDraft, page: 1 });
    }, 300);
    return () => window.clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional debounce on draft
  }, [searchDraft]);

  function updateState(patch: Partial<HazardRegistryUrlState>) {
    const next = { ...state, ...patch };
    const params = serializeRegistrySearchParams(next);
    const queryString = params.toString();
    router.replace(queryString ? `${pathname}?${queryString}` : pathname);
  }

  const columns = useMemo<DataTableColumnDef<Hazard>[]>(
    () => [
      {
        id: "code",
        header: "Код",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/hazards/${row.original.id}`}>
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
        id: "status",
        header: "Статус",
        enableSorting: false,
        cell: ({ row }) => (
          <StatusBadge status={hazardStatusToVisual(row.original.status)} />
        ),
      },
      {
        id: "category",
        header: "Категория",
        enableSorting: false,
        cell: ({ row }) => hazardCategoryLabel(row.original.category),
      },
      {
        id: "location",
        header: "Место",
        enableSorting: false,
        cell: ({ row }) => row.original.locationReference ?? "—",
      },
      {
        id: "updated",
        header: "Обновлено",
        enableSorting: false,
        cell: ({ row }) => formatDate(row.original.updatedAt),
      },
    ],
    [],
  );

  if (!capabilities.canRead) {
    return (
      <PageContainer>
        <EmptyState
          title="Опасности недоступны"
          description="Недостаточно прав для просмотра опасностей."
          action={
            <Button asChild variant="secondary">
              <Link href="/">К обзору</Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  const items = query.data?.items ?? [];
  const total = query.data?.pagination.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  const filteredEmpty =
    !query.isLoading && items.length === 0 && hasActiveRegistryFilters(state);
  const empty =
    !query.isLoading && items.length === 0 && !hasActiveRegistryFilters(state);

  return (
    <PageContainer>
      <PageHeader
        title="Опасности"
        description={
          <Text tone="secondary">
            Выявляйте, классифицируйте и ведите опасности активной организации.
          </Text>
        }
        actions={
          capabilities.canCreate ? (
            <Button asChild>
              <Link href="/safety/hazards/new">Создать опасность</Link>
            </Button>
          ) : null
        }
      />

      <RegistryToolbar
        search={
          <Search
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Поиск по коду, названию, описанию"
            aria-label="Поиск опасностей"
          />
        }
        filters={
          <FilterBar>
            <Select
              aria-label="Фильтр по статусу"
              value={state.status || "__all"}
              onValueChange={(value) =>
                updateState({
                  status:
                    value === "__all"
                      ? ""
                      : (value as HazardRegistryUrlState["status"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все статусы" },
                { value: "draft", label: hazardStatusLabel("draft") },
                { value: "active", label: hazardStatusLabel("active") },
                { value: "archived", label: hazardStatusLabel("archived") },
              ]}
            />
            <Select
              aria-label="Фильтр по категории"
              value={state.category || "__all"}
              onValueChange={(value) =>
                updateState({
                  category:
                    value === "__all"
                      ? ""
                      : (value as HazardRegistryUrlState["category"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все категории" },
                ...HAZARD_CATEGORIES.map((value) => ({
                  value,
                  label: hazardCategoryLabel(value),
                })),
              ]}
            />
            <Select
              aria-label="Фильтр по источнику"
              value={state.source || "__all"}
              onValueChange={(value) =>
                updateState({
                  source:
                    value === "__all"
                      ? ""
                      : (value as HazardRegistryUrlState["source"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все источники" },
                ...HAZARD_SOURCES.map((value) => ({
                  value,
                  label: hazardSourceLabel(value),
                })),
              ]}
            />
            <Button
              type="button"
              variant={state.includeArchived ? "primary" : "secondary"}
              size="sm"
              onClick={() =>
                updateState({
                  includeArchived: !state.includeArchived,
                  page: 1,
                })
              }
            >
              {state.includeArchived ? "Архив включён" : "Включить архив"}
            </Button>
            {state.status ? (
              <FilterChip
                label="Статус"
                value={hazardStatusLabel(state.status)}
                onRemove={() => updateState({ status: "", page: 1 })}
              />
            ) : null}
            {state.category ? (
              <FilterChip
                label="Категория"
                value={hazardCategoryLabel(state.category)}
                onRemove={() => updateState({ category: "", page: 1 })}
              />
            ) : null}
            {state.source ? (
              <FilterChip
                label="Источник"
                value={hazardSourceLabel(state.source)}
                onRemove={() => updateState({ source: "", page: 1 })}
              />
            ) : null}
            {hasActiveRegistryFilters(state) ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => updateState({ ...DEFAULT_REGISTRY_STATE })}
              >
                Сбросить фильтры
              </Button>
            ) : null}
          </FilterBar>
        }
      />

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Не удалось загрузить опасности">
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
        <LoadingState label="Загрузка опасностей" />
      ) : empty ? (
        <EmptyState
          title="Опасностей пока нет"
          description="Создайте первую опасность для этой организации."
          action={
            capabilities.canCreate ? (
              <Button asChild>
                <Link href="/safety/hazards/new">Создать опасность</Link>
              </Button>
            ) : undefined
          }
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="Нет подходящих опасностей"
          description="Измените или сбросьте фильтры."
          action={
            <Button
              variant="secondary"
              onClick={() => updateState({ ...DEFAULT_REGISTRY_STATE })}
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
            emptyMessage="Опасности не найдены"
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
                  Далее
                </Button>
              </RegistryPagination>
            }
          />
        </>
      )}
    </PageContainer>
  );
}
