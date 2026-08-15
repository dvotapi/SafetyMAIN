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
  formatRiskAssessmentEnumLabel,
  riskAssessmentStatusLabel,
  riskAssessmentStatusToVisual,
  riskLevelLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";
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

function profileTitle(code: string): string {
  return (
    ASSESSMENT_PROFILE_CATALOG.find((entry) => entry.code === code)?.title ??
    formatRiskAssessmentEnumLabel(code)
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
    document.title = "Risk Assessments · SafetyMAIN";
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
        header: "Reference",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/risk-assessments/${row.original.id}`}>
            {row.original.code}
          </Link>
        ),
      },
      {
        id: "hazard",
        header: "Hazard",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/hazards/${row.original.hazardId}`}>
            {row.original.hazardId}
          </Link>
        ),
      },
      {
        id: "status",
        header: "Status",
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
        header: "Assessment profile",
        enableSorting: false,
        cell: ({ row }) => profileTitle(String(row.original.assessmentProfile)),
      },
      {
        id: "inherent",
        header: "Inherent risk",
        enableSorting: false,
        cell: ({ row }) =>
          riskLevelLabel(row.original.inherentRisk?.level) ?? "—",
      },
      {
        id: "residual",
        header: "Residual risk",
        enableSorting: false,
        cell: ({ row }) =>
          riskLevelLabel(row.original.residualRisk?.level) ?? "—",
      },
      {
        id: "nextReview",
        header: "Next review",
        enableSorting: false,
        cell: ({ row }) =>
          formatDate(row.original.reviewSchedule.reviewDueDate),
      },
      {
        id: "approvedAt",
        header: "Approved at",
        enableSorting: false,
        cell: ({ row }) => formatDate(row.original.approvedAt),
      },
      {
        id: "updatedAt",
        header: "Updated at",
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
          title="Risk assessments unavailable"
          description="You do not have permission to view risk assessments."
          action={
            <Button asChild variant="secondary">
              <Link href="/">Back to overview</Link>
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
        title="Risk Assessments"
        description={
          <Text tone="secondary">
            Create and review risk assessments for hazards in the active
            organization. Ordering is fixed by the server (newest first).
          </Text>
        }
        actions={
          capabilities.canCreate ? (
            <Button asChild>
              <Link href="/safety/risk-assessments/new">
                Create risk assessment
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
            placeholder="Search code or title"
            aria-label="Search risk assessments"
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
                      : (value as RiskAssessmentRegistryUrlState["status"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "All statuses" },
                { value: "draft", label: "Draft" },
                { value: "under_review", label: "Under Review" },
                { value: "approved", label: "Approved" },
                { value: "superseded", label: "Superseded" },
                { value: "archived", label: "Archived" },
              ]}
            />
            <Select
              aria-label="Assessment profile filter"
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
                { value: "__all", label: "All profiles" },
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
              {state.includeArchived
                ? "Including archived"
                : "Include archived"}
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
                ? "Including superseded"
                : "Hide superseded"}
            </Button>
            {state.status ? (
              <FilterChip
                label="Status"
                value={riskAssessmentStatusLabel(state.status)}
                onRemove={() => updateState({ status: "", page: 1 })}
              />
            ) : null}
            {state.assessmentProfile ? (
              <FilterChip
                label="Profile"
                value={profileTitle(state.assessmentProfile)}
                onRemove={() => updateState({ assessmentProfile: "", page: 1 })}
              />
            ) : null}
            {state.hazardId ? (
              <FilterChip
                label="Hazard"
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
                Clear filters
              </Button>
            ) : null}
          </FilterBar>
        }
      />

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Unable to load risk assessments">
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
        <LoadingState label="Loading risk assessments" />
      ) : empty ? (
        <EmptyState
          title="No risk assessments yet"
          description="Create the first risk assessment for this organization."
          action={
            capabilities.canCreate ? (
              <Button asChild>
                <Link href="/safety/risk-assessments/new">
                  Create risk assessment
                </Link>
              </Button>
            ) : undefined
          }
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="No matching risk assessments"
          description="Try adjusting or clearing filters."
          action={
            <Button
              variant="secondary"
              onClick={() =>
                updateState({ ...DEFAULT_RISK_ASSESSMENT_REGISTRY_STATE })
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
            emptyMessage="No risk assessments found"
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
