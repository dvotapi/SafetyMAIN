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
import { useRiskAssessmentListQuery } from "@/features/risk-assessments/api/risk-assessment-queries";
import { mapRiskAssessmentCapabilities } from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import { ASSESSMENT_PROFILES } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type { RiskAssessment } from "@/features/risk-assessments/types/risk-assessment-types";
import { ASSESSMENT_PROFILE_CATALOG } from "@/features/risk-assessments/utils/assessment-profiles";
import {
  DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE,
  hasActiveRiskAssessmentRegistryFilters,
  parseRiskAssessmentRegistrySearchParams,
  registryStateToListParams,
  serializeRiskAssessmentRegistrySearchParams,
  type RiskAssessmentRegistryUrlState,
} from "@/features/risk-assessments/utils/risk-assessment-filters";
import {
  assessmentProfileLabel,
  riskAssessmentStatusLabel,
  riskAssessmentStatusToVisual,
  riskLevelLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";
import { useAuth } from "@/hooks/auth";
import { toUserSafeMessage } from "@/services/api/errors";
import { APP_LOCALE } from "@/utils/locale";

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(APP_LOCALE, {
      dateStyle: "medium",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function profileTitle(code: string): string {
  return (
    ASSESSMENT_PROFILE_CATALOG.find((entry) => entry.code === code)?.title ??
    assessmentProfileLabel(code)
  );
}

export function RiskAssessmentRegistryPage() {
  const { hasPermission } = useAuth();
  const capabilities = mapRiskAssessmentCapabilities(hasPermission);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const state = useMemo(
    () =>
      parseRiskAssessmentRegistrySearchParams(
        new URLSearchParams(searchParams.toString()),
      ),
    [searchParams],
  );
  const listParams = useMemo(() => registryStateToListParams(state), [state]);
  const query = useRiskAssessmentListQuery(listParams, capabilities.canRead);
  const [searchDraft, setSearchDraft] = useState(state.search);

  useEffect(() => {
    document.title = "Оценки риска · SafetyMAIN";
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

  function updateState(patch: Partial<RiskAssessmentRegistryUrlState>) {
    const next = { ...state, ...patch };
    const params = serializeRiskAssessmentRegistrySearchParams(next);
    const queryString = params.toString();
    router.replace(queryString ? `${pathname}?${queryString}` : pathname);
  }

  const columns = useMemo<DataTableColumnDef<RiskAssessment>[]>(
    () => [
      {
        id: "code",
        header: "Код",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/risk-assessments/${row.original.id}`}>
            {row.original.code}
          </Link>
        ),
      },
      {
        id: "hazard",
        header: "Опасность",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/hazards/${row.original.hazardId}`}>
            {row.original.hazardId}
          </Link>
        ),
      },
      {
        id: "status",
        header: "Статус",
        enableSorting: false,
        cell: ({ row }) => (
          <StatusBadge
            status={riskAssessmentStatusToVisual(row.original.status)}
            label={riskAssessmentStatusLabel(row.original.status)}
          />
        ),
      },
      {
        id: "profile",
        header: "Профиль оценки",
        enableSorting: false,
        cell: ({ row }) => profileTitle(String(row.original.assessmentProfile)),
      },
      {
        id: "inherent",
        header: "Исходный риск",
        enableSorting: false,
        cell: ({ row }) =>
          riskLevelLabel(row.original.inherentRisk?.level) ?? "—",
      },
      {
        id: "residual",
        header: "Остаточный риск",
        enableSorting: false,
        cell: ({ row }) =>
          riskLevelLabel(row.original.residualRisk?.level) ?? "—",
      },
      {
        id: "nextReview",
        header: "Следующий пересмотр",
        enableSorting: false,
        cell: ({ row }) =>
          formatDate(row.original.reviewSchedule.reviewDueDate),
      },
      {
        id: "approvedAt",
        header: "Утверждено",
        enableSorting: false,
        cell: ({ row }) => formatDate(row.original.approvedAt),
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
          title="Оценки риска недоступны"
          description="Недостаточно прав для просмотра оценок риска."
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
    !query.isLoading &&
    items.length === 0 &&
    hasActiveRiskAssessmentRegistryFilters(state);
  const empty =
    !query.isLoading &&
    items.length === 0 &&
    !hasActiveRiskAssessmentRegistryFilters(state);

  return (
    <PageContainer>
      <PageHeader
        title="Оценки риска"
        description={
          <Text tone="secondary">
            Создавайте и просматривайте оценки риска для опасностей активной
            организации. Порядок сортировки задаётся сервером (сначала новые).
          </Text>
        }
        actions={
          capabilities.canCreate ? (
            <Button asChild>
              <Link href="/safety/risk-assessments/new">
                Создать оценку риска
              </Link>
            </Button>
          ) : null
        }
      />

      <RegistryToolbar
        search={
          <Search
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Поиск по коду или названию"
            aria-label="Поиск оценок риска"
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
                      : (value as RiskAssessmentRegistryUrlState["status"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все статусы" },
                { value: "draft", label: riskAssessmentStatusLabel("draft") },
                {
                  value: "under_review",
                  label: riskAssessmentStatusLabel("under_review"),
                },
                {
                  value: "approved",
                  label: riskAssessmentStatusLabel("approved"),
                },
                {
                  value: "superseded",
                  label: riskAssessmentStatusLabel("superseded"),
                },
                {
                  value: "archived",
                  label: riskAssessmentStatusLabel("archived"),
                },
              ]}
            />
            <Select
              aria-label="Фильтр по профилю оценки"
              value={state.assessmentProfile || "__all"}
              onValueChange={(value) =>
                updateState({
                  assessmentProfile:
                    value === "__all"
                      ? ""
                      : (value as RiskAssessmentRegistryUrlState["assessmentProfile"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "Все профили" },
                ...ASSESSMENT_PROFILES.map((code) => ({
                  value: code,
                  label: profileTitle(code),
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
            <Button
              type="button"
              variant={state.includeSuperseded ? "primary" : "secondary"}
              size="sm"
              onClick={() =>
                updateState({
                  includeSuperseded: !state.includeSuperseded,
                  page: 1,
                })
              }
            >
              {state.includeSuperseded
                ? "Замещённые включены"
                : "Скрыть замещённые"}
            </Button>
            {state.status ? (
              <FilterChip
                label="Статус"
                value={riskAssessmentStatusLabel(state.status)}
                onRemove={() => updateState({ status: "", page: 1 })}
              />
            ) : null}
            {state.assessmentProfile ? (
              <FilterChip
                label="Профиль"
                value={profileTitle(state.assessmentProfile)}
                onRemove={() => updateState({ assessmentProfile: "", page: 1 })}
              />
            ) : null}
            {state.hazardId ? (
              <FilterChip
                label="Опасность"
                value={state.hazardId}
                onRemove={() => updateState({ hazardId: "", page: 1 })}
              />
            ) : null}
            {hasActiveRiskAssessmentRegistryFilters(state) ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() =>
                  updateState({ ...DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE })
                }
              >
                Сбросить фильтры
              </Button>
            ) : null}
          </FilterBar>
        }
      />

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Не удалось загрузить оценки риска">
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
        <LoadingState label="Загрузка оценок риска" />
      ) : empty ? (
        <EmptyState
          title="Оценок риска пока нет"
          description="Создайте первую оценку риска для этой организации."
          action={
            capabilities.canCreate ? (
              <Button asChild>
                <Link href="/safety/risk-assessments/new">
                  Создать оценку риска
                </Link>
              </Button>
            ) : undefined
          }
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="Нет подходящих оценок риска"
          description="Измените или сбросьте фильтры."
          action={
            <Button
              variant="secondary"
              onClick={() =>
                updateState({ ...DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE })
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
            emptyMessage="Оценки риска не найдены"
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
