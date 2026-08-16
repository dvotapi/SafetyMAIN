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
import { useRiskControlListQuery } from "@/features/risk-controls/api/risk-control-queries";
import { mapRiskControlCapabilities } from "@/features/risk-controls/hooks/use-risk-control-permissions";
import type { RiskControl } from "@/features/risk-controls/types/risk-control-types";
import {
  CONTROL_NATURES,
  EFFECTIVENESS_FILTER_VALUES,
  HIERARCHY_LEVELS,
  RISK_CONTROL_STATUSES,
  effectivenessLabel,
  effectivenessToVisual,
  formatRiskControlEnumLabel,
  implementationStateLabel,
  riskControlStatusLabel,
  riskControlStatusToVisual,
} from "@/features/risk-controls/utils/risk-control-status";
import {
  DEFAULT_RISK_CONTROL_REGISTRY_STATE,
  hasActiveRiskControlRegistryFilters,
  parseRiskControlRegistrySearchParams,
  registryStateToListParams,
  serializeRiskControlRegistrySearchParams,
  type RiskControlRegistryUrlState,
} from "@/features/risk-controls/utils/risk-control-filters";
import { useAuth } from "@/hooks/auth";
import { toUserSafeMessage } from "@/services/api/errors";

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function RiskControlRegistryPage() {
  const { hasPermission } = useAuth();
  const capabilities = mapRiskControlCapabilities(hasPermission);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const state = useMemo(
    () =>
      parseRiskControlRegistrySearchParams(
        new URLSearchParams(searchParams.toString()),
      ),
    [searchParams],
  );
  const listParams = useMemo(() => registryStateToListParams(state), [state]);
  const query = useRiskControlListQuery(listParams, capabilities.canRead);
  const [searchDraft, setSearchDraft] = useState(state.search);

  useEffect(() => {
    document.title = "Меры управления риском · SafetyMAIN";
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

  function updateState(patch: Partial<RiskControlRegistryUrlState>) {
    const next = { ...state, ...patch };
    const params = serializeRiskControlRegistrySearchParams(next);
    const queryString = params.toString();
    router.replace(queryString ? `${pathname}?${queryString}` : pathname);
  }

  const items = query.data?.items ?? [];
  const total = query.data?.pagination.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));

  useEffect(() => {
    if (query.data && state.page > totalPages && totalPages >= 1) {
      updateState({ page: totalPages });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- self-correct stale deep links only
  }, [state.page, totalPages, query.data]);

  const columns = useMemo<DataTableColumnDef<RiskControl>[]>(
    () => [
      {
        id: "code",
        header: "Код",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/risk-controls/${row.original.id}`}>
            {row.original.code}
          </Link>
        ),
      },
      {
        id: "title",
        header: "Мера",
        enableSorting: false,
        cell: ({ row }) => row.original.title,
      },
      {
        id: "hierarchy",
        header: "Уровень иерархии",
        enableSorting: false,
        cell: ({ row }) =>
          formatRiskControlEnumLabel(row.original.hierarchyLevel),
      },
      {
        id: "status",
        header: "Статус",
        enableSorting: false,
        cell: ({ row }) => (
          <StatusBadge
            status={riskControlStatusToVisual(row.original.status)}
            label={riskControlStatusLabel(row.original.status)}
          />
        ),
      },
      {
        id: "owner",
        header: "Владелец",
        enableSorting: false,
        cell: ({ row }) => row.original.owner?.label ?? "Не назначен",
      },
      {
        id: "implementation",
        header: "Внедрение",
        enableSorting: false,
        cell: ({ row }) =>
          implementationStateLabel({
            status: row.original.status,
            progress: row.original.implementation.progress,
            actualCompletionDate:
              row.original.implementation.actualCompletionDate,
          }),
      },
      {
        id: "effectiveness",
        header: "Эффективность",
        enableSorting: false,
        cell: ({ row }) => {
          const visual = effectivenessToVisual(
            row.original.latestEffectivenessResult,
          );
          if (!visual) {
            return "Не подтверждена";
          }
          return (
            <StatusBadge
              status={visual}
              label={effectivenessLabel(row.original.latestEffectivenessResult)}
            />
          );
        },
      },
      {
        id: "hazard",
        header: "Опасность",
        enableSorting: false,
        cell: ({ row }) =>
          row.original.hazardId ? (
            <Link href={`/safety/hazards/${row.original.hazardId}`}>
              {row.original.hazardId}
            </Link>
          ) : (
            "—"
          ),
      },
      {
        id: "assessment",
        header: "Оценка риска",
        enableSorting: false,
        cell: ({ row }) =>
          row.original.riskAssessmentId ? (
            <Link
              href={`/safety/risk-assessments/${row.original.riskAssessmentId}`}
            >
              {row.original.riskAssessmentId}
            </Link>
          ) : (
            "—"
          ),
      },
      {
        id: "nextReview",
        header: "Следующий пересмотр",
        enableSorting: false,
        cell: ({ row }) => formatDate(row.original.nextReviewDate),
      },
      {
        id: "overdue",
        header: "Просрочено",
        enableSorting: false,
        cell: ({ row }) =>
          row.original.isOverdue ? (
            <StatusBadge status="overdue" label="Просрочено" />
          ) : (
            "—"
          ),
      },
      {
        id: "updatedAt",
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
          title="Меры управления риском недоступны"
          description="Недостаточно прав для просмотра мер управления риском."
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
    hasActiveRiskControlRegistryFilters(state);
  const empty =
    !query.isLoading &&
    items.length === 0 &&
    !hasActiveRiskControlRegistryFilters(state);

  return (
    <PageContainer>
      <PageHeader
        title="Меры управления риском"
        description={
          <Text tone="secondary">
            Операционные меры управления риском активной организации. Порядок
            задаёт сервер (сначала новые).
          </Text>
        }
      />

      <RegistryToolbar
        search={
          <Search
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Поиск по коду, названию или описанию"
            aria-label="Поиск мер управления риском"
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
                      : (value as RiskControlRegistryUrlState["status"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все статусы" },
                ...RISK_CONTROL_STATUSES.map((status) => ({
                  value: status,
                  label: riskControlStatusLabel(status),
                })),
              ]}
            />
            <Select
              aria-label="Фильтр по уровню иерархии"
              value={state.hierarchyLevel || "__all"}
              onValueChange={(value) =>
                updateState({
                  hierarchyLevel:
                    value === "__all"
                      ? ""
                      : (value as RiskControlRegistryUrlState["hierarchyLevel"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все уровни иерархии" },
                ...HIERARCHY_LEVELS.map((level) => ({
                  value: level,
                  label: formatRiskControlEnumLabel(level),
                })),
              ]}
            />
            <Select
              aria-label="Фильтр по характеру меры"
              value={state.controlNature || "__all"}
              onValueChange={(value) =>
                updateState({
                  controlNature:
                    value === "__all"
                      ? ""
                      : (value as RiskControlRegistryUrlState["controlNature"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все характеры меры" },
                ...CONTROL_NATURES.map((nature) => ({
                  value: nature,
                  label: formatRiskControlEnumLabel(nature),
                })),
              ]}
            />
            <Select
              aria-label="Фильтр по эффективности"
              value={state.effectiveness || "__all"}
              onValueChange={(value) =>
                updateState({
                  effectiveness:
                    value === "__all"
                      ? ""
                      : (value as RiskControlRegistryUrlState["effectiveness"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все результаты эффективности" },
                ...EFFECTIVENESS_FILTER_VALUES.map((result) => ({
                  value: result,
                  label: effectivenessLabel(result),
                })),
              ]}
            />
            <Button
              type="button"
              variant={state.overdueOnly ? "primary" : "secondary"}
              size="sm"
              onClick={() =>
                updateState({ overdueOnly: !state.overdueOnly, page: 1 })
              }
            >
              Только просроченные
            </Button>
            <Button
              type="button"
              variant={state.awaitingVerification ? "primary" : "secondary"}
              size="sm"
              onClick={() =>
                updateState({
                  awaitingVerification: !state.awaitingVerification,
                  page: 1,
                })
              }
            >
              Ожидает подтверждения
            </Button>
            <Button
              type="button"
              variant={state.includeTerminal ? "primary" : "secondary"}
              size="sm"
              onClick={() =>
                updateState({
                  includeTerminal: !state.includeTerminal,
                  page: 1,
                })
              }
            >
              Показать закрытые
            </Button>
            {state.status ? (
              <FilterChip
                label="Статус"
                value={riskControlStatusLabel(state.status)}
                onRemove={() => updateState({ status: "", page: 1 })}
              />
            ) : null}
            {state.hierarchyLevel ? (
              <FilterChip
                label="Иерархия"
                value={formatRiskControlEnumLabel(state.hierarchyLevel)}
                onRemove={() => updateState({ hierarchyLevel: "", page: 1 })}
              />
            ) : null}
            {state.controlNature ? (
              <FilterChip
                label="Характер"
                value={formatRiskControlEnumLabel(state.controlNature)}
                onRemove={() => updateState({ controlNature: "", page: 1 })}
              />
            ) : null}
            {state.effectiveness ? (
              <FilterChip
                label="Эффективность"
                value={effectivenessLabel(state.effectiveness)}
                onRemove={() => updateState({ effectiveness: "", page: 1 })}
              />
            ) : null}
            {state.overdueOnly ? (
              <FilterChip
                label="Просрочено"
                value="Только просроченные"
                onRemove={() => updateState({ overdueOnly: false, page: 1 })}
              />
            ) : null}
            {state.awaitingVerification ? (
              <FilterChip
                label="Подтверждение"
                value="Ожидает подтверждения"
                onRemove={() =>
                  updateState({ awaitingVerification: false, page: 1 })
                }
              />
            ) : null}
            {state.includeTerminal ? (
              <FilterChip
                label="Закрытые"
                value="Включено"
                onRemove={() =>
                  updateState({ includeTerminal: false, page: 1 })
                }
              />
            ) : null}
            {hasActiveRiskControlRegistryFilters(state) ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() =>
                  updateState({ ...DEFAULT_RISK_CONTROL_REGISTRY_STATE })
                }
              >
                Сбросить фильтры
              </Button>
            ) : null}
          </FilterBar>
        }
      />

      {state.includeTerminal ? null : (
        <Text tone="muted" variant="caption">
          Замещённые, архивные и отменённые меры по умолчанию скрыты.
        </Text>
      )}

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert
            tone="danger"
            title="Не удалось загрузить меры управления риском"
          >
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
        <LoadingState label="Загрузка мер управления риском" />
      ) : empty ? (
        <EmptyState
          title="Мер управления риском пока нет"
          description="Меры появятся здесь после создания из утверждённой оценки риска."
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="Нет подходящих мер управления риском"
          description="Измените или сбросьте фильтры."
          action={
            <Button
              variant="secondary"
              onClick={() =>
                updateState({ ...DEFAULT_RISK_CONTROL_REGISTRY_STATE })
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
            emptyMessage="Меры управления риском не найдены"
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
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={state.page >= totalPages}
                  onClick={() => updateState({ page: state.page + 1 })}
                >
                  Next
                </Button>
              </RegistryPagination>
            }
          />
        </>
      )}
    </PageContainer>
  );
}
