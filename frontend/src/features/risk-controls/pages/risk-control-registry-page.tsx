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
    document.title = "Risk Controls · SafetyMAIN";
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
    if (state.page > totalPages && totalPages >= 1) {
      updateState({ page: totalPages });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- self-correct stale deep links only
  }, [state.page, totalPages]);

  const columns = useMemo<DataTableColumnDef<RiskControl>[]>(
    () => [
      {
        id: "code",
        header: "Reference",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/risk-controls/${row.original.id}`}>
            {row.original.code}
          </Link>
        ),
      },
      {
        id: "title",
        header: "Control",
        enableSorting: false,
        cell: ({ row }) => row.original.title,
      },
      {
        id: "hierarchy",
        header: "Hierarchy Level",
        enableSorting: false,
        cell: ({ row }) =>
          formatRiskControlEnumLabel(row.original.hierarchyLevel),
      },
      {
        id: "status",
        header: "Status",
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
        header: "Owner",
        enableSorting: false,
        cell: ({ row }) => row.original.owner?.label ?? "Unassigned",
      },
      {
        id: "implementation",
        header: "Implementation",
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
        header: "Effectiveness",
        enableSorting: false,
        cell: ({ row }) => {
          const visual = effectivenessToVisual(
            row.original.latestEffectivenessResult,
          );
          if (!visual) {
            return "Not verified";
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
        header: "Hazard",
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
        header: "Risk Assessment",
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
        header: "Next Review",
        enableSorting: false,
        cell: ({ row }) => formatDate(row.original.nextReviewDate),
      },
      {
        id: "overdue",
        header: "Overdue",
        enableSorting: false,
        cell: ({ row }) =>
          row.original.isOverdue ? (
            <StatusBadge status="overdue" label="Overdue" />
          ) : (
            "—"
          ),
      },
      {
        id: "updatedAt",
        header: "Updated At",
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
          title="Risk controls unavailable"
          description="You do not have permission to view risk controls."
          action={
            <Button asChild variant="secondary">
              <Link href="/">Back to overview</Link>
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
        title="Risk Controls"
        description={
          <Text tone="secondary">
            Operational risk controls for the active organization. Ordering is
            fixed by the server (newest first).
          </Text>
        }
      />

      <RegistryToolbar
        search={
          <Search
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Search code, title or description"
            aria-label="Search risk controls"
          />
        }
        filters={
          <FilterBar>
            <Select
              aria-label="Status filter"
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
                { value: "__all", label: "All statuses" },
                ...RISK_CONTROL_STATUSES.map((status) => ({
                  value: status,
                  label: riskControlStatusLabel(status),
                })),
              ]}
            />
            <Select
              aria-label="Hierarchy level filter"
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
                { value: "__all", label: "All hierarchy levels" },
                ...HIERARCHY_LEVELS.map((level) => ({
                  value: level,
                  label: formatRiskControlEnumLabel(level),
                })),
              ]}
            />
            <Select
              aria-label="Control nature filter"
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
                { value: "__all", label: "All control natures" },
                ...CONTROL_NATURES.map((nature) => ({
                  value: nature,
                  label: formatRiskControlEnumLabel(nature),
                })),
              ]}
            />
            <Select
              aria-label="Effectiveness filter"
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
                { value: "__all", label: "All effectiveness results" },
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
              Overdue only
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
              Awaiting verification
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
              Include closed
            </Button>
            {state.status ? (
              <FilterChip
                label="Status"
                value={riskControlStatusLabel(state.status)}
                onRemove={() => updateState({ status: "", page: 1 })}
              />
            ) : null}
            {state.hierarchyLevel ? (
              <FilterChip
                label="Hierarchy"
                value={formatRiskControlEnumLabel(state.hierarchyLevel)}
                onRemove={() => updateState({ hierarchyLevel: "", page: 1 })}
              />
            ) : null}
            {state.controlNature ? (
              <FilterChip
                label="Nature"
                value={formatRiskControlEnumLabel(state.controlNature)}
                onRemove={() => updateState({ controlNature: "", page: 1 })}
              />
            ) : null}
            {state.effectiveness ? (
              <FilterChip
                label="Effectiveness"
                value={effectivenessLabel(state.effectiveness)}
                onRemove={() => updateState({ effectiveness: "", page: 1 })}
              />
            ) : null}
            {state.overdueOnly ? (
              <FilterChip
                label="Overdue"
                value="Overdue only"
                onRemove={() => updateState({ overdueOnly: false, page: 1 })}
              />
            ) : null}
            {state.awaitingVerification ? (
              <FilterChip
                label="Verification"
                value="Awaiting verification"
                onRemove={() =>
                  updateState({ awaitingVerification: false, page: 1 })
                }
              />
            ) : null}
            {state.includeTerminal ? (
              <FilterChip
                label="Closed"
                value="Included"
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
                Clear filters
              </Button>
            ) : null}
          </FilterBar>
        }
      />

      {state.includeTerminal ? null : (
        <Text tone="muted" variant="caption">
          Superseded, archived and cancelled controls are hidden by default.
        </Text>
      )}

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Unable to load risk controls">
            {toUserSafeMessage(query.error)}
          </Alert>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void query.refetch()}
          >
            Retry
          </Button>
        </div>
      ) : null}

      {query.isLoading && !query.data ? (
        <LoadingState label="Loading risk controls" />
      ) : empty ? (
        <EmptyState
          title="No risk controls yet"
          description="Risk controls appear here once they are materialized from an approved risk assessment."
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="No matching risk controls"
          description="Try adjusting or clearing filters."
          action={
            <Button
              variant="secondary"
              onClick={() =>
                updateState({ ...DEFAULT_RISK_CONTROL_REGISTRY_STATE })
              }
            >
              Clear filters
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
            emptyMessage="No risk controls found"
          />
          <RegistryFooter
            pagination={
              <RegistryPagination
                summary={
                  <Text tone="muted" variant="caption">
                    {total} total · page {state.page} of {totalPages}
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
