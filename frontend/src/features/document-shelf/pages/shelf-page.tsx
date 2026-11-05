"use client";

import { useEffect, useMemo } from "react";

import { Alert, Button, EmptyState, Skeleton } from "@/components";

import {
  useShelfOverviewQuery,
  useShelfSectionSlotsQuery,
} from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";
import { OpenedShelf } from "@/features/document-shelf/components/opened-shelf";
import { ShelfHeader } from "@/features/document-shelf/components/shelf-header";
import { ShelfOverview } from "@/features/document-shelf/components/shelf-overview";
import { ShelfSummary } from "@/features/document-shelf/components/shelf-summary";
import { useShelfPermissions } from "@/features/document-shelf/hooks/use-shelf-permissions";
import { useShelfUrlState } from "@/features/document-shelf/hooks/use-shelf-url-state";
import { toUserSafeMessage } from "@/services/api/errors";

export const SHELF_IMPORT_GUIDE_URL =
  "https://github.com/dvotapi/SafetyMAIN/blob/main/docs/guides/ShelfImport.md";

export function ShelfPage() {
  const capabilities = useShelfPermissions();
  const { state, openSection, selectSlot, setFilter, setExcludedHidden } =
    useShelfUrlState();
  const overview = useShelfOverviewQuery(capabilities.canRead);
  const section = useShelfSectionSlotsQuery(state.section);

  useEffect(() => {
    document.title = "Полка документов · SafetyMAIN";
  }, []);

  const openedSummary = useMemo(
    () => overview.data?.sections.find((item) => item.code === state.section),
    [overview.data, state.section],
  );

  if (!capabilities.canRead) {
    return (
      <div className={styles.page}>
        <Alert tone="warning" title="Нет доступа">
          У вас нет права просматривать полку документов.
        </Alert>
      </div>
    );
  }

  if (overview.isError) {
    return (
      <div className={styles.page}>
        <Alert tone="danger" title="Не удалось загрузить полку">
          {toUserSafeMessage(overview.error)}{" "}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void overview.refetch()}
          >
            Повторить
          </Button>
        </Alert>
      </div>
    );
  }

  if (overview.isPending) {
    return (
      <div className={styles.page} aria-busy="true" aria-label="Загрузка полки">
        <Skeleton height="56px" />
        <Skeleton height="88px" />
        {[0, 1, 2, 3, 4].map((index) => (
          <Skeleton key={index} height="34px" />
        ))}
      </div>
    );
  }

  const data = overview.data;
  if (data.sections.length === 0) {
    return (
      <div className={styles.page}>
        <EmptyState
          title="Загрузите реестр-полку"
          description="Полка пока пуста. Куратор загружает реестр документов из книги Excel."
          action={
            <a href={SHELF_IMPORT_GUIDE_URL} target="_blank" rel="noreferrer">
              Как загрузить реестр
            </a>
          }
        />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <ShelfHeader
        overview={data}
        filter={state.filter}
        excludedHidden={state.excludedHidden}
        onFilterChange={setFilter}
        onExcludedHiddenChange={setExcludedHidden}
      />
      <ShelfSummary totals={data.totals} />
      <div
        className={styles.layout}
        // The place panel (right column ≥ 1200 px) arrives in PR 4c.
        data-panel="closed"
      >
        <div style={{ display: "grid", gap: "var(--sm-space-6)", minWidth: 0 }}>
          <ShelfOverview
            sections={data.sections}
            openSection={state.section}
            filter={state.filter}
            excludedHidden={state.excludedHidden}
            onToggle={(code) => {
              if (code === state.section) {
                openSection(null);
                return;
              }
              const first = data.sections.find((item) => item.code === code)
                ?.strip[0];
              openSection(code, first?.code ?? null);
            }}
          />
          {openedSummary ? (
            <OpenedShelf
              summary={openedSummary}
              data={section.data}
              loading={section.isPending}
              error={section.isError ? toUserSafeMessage(section.error) : null}
              onRetry={() => void section.refetch()}
              selectedSlot={state.slot}
              filter={state.filter}
              excludedHidden={state.excludedHidden}
              onSelect={(slot) => selectSlot(slot.code)}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
