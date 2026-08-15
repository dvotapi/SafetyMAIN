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
  formatHazardEnumLabel,
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

function formatDate(value: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
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
    document.title = "Hazards · SafetyMAIN";
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
        header: "Reference",
        enableSorting: false,
        cell: ({ row }) => (
          <Link href={`/safety/hazards/${row.original.id}`}>
            {row.original.code}
          </Link>
        ),
      },
      {
        id: "title",
        header: "Title",
        enableSorting: false,
        cell: ({ row }) => row.original.title,
      },
      {
        id: "status",
        header: "Status",
        enableSorting: false,
        cell: ({ row }) => (
          <StatusBadge status={hazardStatusToVisual(row.original.status)} />
        ),
      },
      {
        id: "category",
        header: "Category",
        enableSorting: false,
        cell: ({ row }) => formatHazardEnumLabel(row.original.category),
      },
      {
        id: "location",
        header: "Location",
        enableSorting: false,
        cell: ({ row }) => row.original.locationReference ?? "—",
      },
      {
        id: "updated",
        header: "Last updated",
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
          title="Hazards unavailable"
          description="You do not have permission to view hazards."
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
    !query.isLoading && items.length === 0 && hasActiveRegistryFilters(state);
  const empty =
    !query.isLoading && items.length === 0 && !hasActiveRegistryFilters(state);

  return (
    <PageContainer>
      <PageHeader
        title="Hazards"
        description={
          <Text tone="secondary">
            Identify, classify, and manage hazards for the active organization.
          </Text>
        }
        actions={
          capabilities.canCreate ? (
            <Button asChild>
              <Link href="/safety/hazards/new">Create hazard</Link>
            </Button>
          ) : null
        }
      />

      <RegistryToolbar
        search={
          <Search
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Search code, title, description"
            aria-label="Search hazards"
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
                      : (value as HazardRegistryUrlState["status"]),
                  page: 1,
                })
              }
              options={[
                { value: "__all", label: "All statuses" },
                { value: "draft", label: "Draft" },
                { value: "active", label: "Active" },
                { value: "archived", label: "Archived" },
              ]}
            />
            <Select
              aria-label="Category filter"
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
                { value: "__all", label: "All categories" },
                ...HAZARD_CATEGORIES.map((value) => ({
                  value,
                  label: formatHazardEnumLabel(value),
                })),
              ]}
            />
            <Select
              aria-label="Source filter"
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
                { value: "__all", label: "All sources" },
                ...HAZARD_SOURCES.map((value) => ({
                  value,
                  label: formatHazardEnumLabel(value),
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
            {state.status ? (
              <FilterChip
                label="Status"
                value={state.status}
                onRemove={() => updateState({ status: "", page: 1 })}
              />
            ) : null}
            {state.category ? (
              <FilterChip
                label="Category"
                value={formatHazardEnumLabel(state.category)}
                onRemove={() => updateState({ category: "", page: 1 })}
              />
            ) : null}
            {state.source ? (
              <FilterChip
                label="Source"
                value={formatHazardEnumLabel(state.source)}
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
                Clear filters
              </Button>
            ) : null}
          </FilterBar>
        }
      />

      {query.isError ? (
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Unable to load hazards">
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
        <LoadingState label="Loading hazards" />
      ) : empty ? (
        <EmptyState
          title="No hazards yet"
          description="Create the first hazard for this organization."
          action={
            capabilities.canCreate ? (
              <Button asChild>
                <Link href="/safety/hazards/new">Create hazard</Link>
              </Button>
            ) : undefined
          }
        />
      ) : filteredEmpty ? (
        <EmptyState
          title="No matching hazards"
          description="Try adjusting or clearing filters."
          action={
            <Button
              variant="secondary"
              onClick={() => updateState({ ...DEFAULT_REGISTRY_STATE })}
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
            emptyMessage="No hazards found"
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
