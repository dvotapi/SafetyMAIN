"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Alert, Button, EmptyState, Skeleton, TextButton } from "@/components";

import {
  useShelfOverviewQuery,
  useShelfSectionSlotsQuery,
} from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";
import { OpenedShelf } from "@/features/document-shelf/components/opened-shelf";
import { ShelfHeader } from "@/features/document-shelf/components/shelf-header";
import { ShelfExclusionForm } from "@/features/document-shelf/components/shelf-exclusion-form";
import { ShelfOverview } from "@/features/document-shelf/components/shelf-overview";
import { ShelfPlacePanel } from "@/features/document-shelf/components/shelf-place-panel";
import { ShelfSearch } from "@/features/document-shelf/components/shelf-search";
import { ShelfSummary } from "@/features/document-shelf/components/shelf-summary";
import { useShelfPermissions } from "@/features/document-shelf/hooks/use-shelf-permissions";
import { useShelfUrlState } from "@/features/document-shelf/hooks/use-shelf-url-state";
import {
  BULK_EXCLUDE_MAX_ITEMS,
  useBulkExcludeShelfSlotsMutation,
  useRestoreShelfSlotsMutation,
} from "@/features/document-shelf/api/shelf-mutations";
import { shelfErrorMessage } from "@/features/document-shelf/utils/shelf-errors";
import { pluralPlaces } from "@/features/document-shelf/utils/shelf-labels";
import { toUserSafeMessage } from "@/services/api/errors";

export const SHELF_IMPORT_GUIDE_URL =
  "https://github.com/dvotapi/SafetyMAIN/blob/main/docs/guides/ShelfImport.md";

export function ShelfPage() {
  const capabilities = useShelfPermissions();
  const { state, openSection, selectSlot, setFilter, setExcludedHidden } =
    useShelfUrlState();
  const overview = useShelfOverviewQuery(capabilities.canRead);
  const section = useShelfSectionSlotsQuery(state.section);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selected, setSelected] = useState<
    Map<string, { code: string; version: number }>
  >(new Map());
  const [bulkForm, setBulkForm] = useState(false);
  const [bulkError, setBulkError] = useState<string | null>(null);
  const [undo, setUndo] = useState<{
    codes: string[];
    slotIds: string[];
  } | null>(null);
  const [undoError, setUndoError] = useState<string | null>(null);
  const bulkExclude = useBulkExcludeShelfSlotsMutation();
  const restoreMany = useRestoreShelfSlotsMutation();

  const selectedSlotId = useMemo(() => {
    for (const subsection of section.data?.subsections ?? []) {
      const found = subsection.slots.find((slot) => slot.code === state.slot);
      if (found) return found.id;
    }
    return null;
  }, [section.data, state.slot]);

  const resetSelection = useCallback(() => {
    setSelectionMode(false);
    setSelected(new Map());
    setBulkForm(false);
    setBulkError(null);
  }, []);

  useEffect(() => {
    resetSelection();
  }, [state.section, resetSelection]);

  const closePanel = useCallback(() => {
    const code = state.slot;
    selectSlot(null);
    // Focus returns to the spine of the closed place (§4.4).
    window.requestAnimationFrame(() => {
      if (code) {
        document
          .querySelector<HTMLButtonElement>(`[data-code="${code}"]`)
          ?.focus();
      }
    });
  }, [selectSlot, state.slot]);

  useEffect(() => {
    if (!state.slot) return undefined;
    function onKey(event: KeyboardEvent) {
      if (event.key !== "Escape" || event.defaultPrevented) return;
      if (document.querySelector("[role=dialog]")) return;
      // Escape inside a field or the search box belongs to that control.
      const target = event.target as HTMLElement | null;
      if (
        target?.closest(
          "input, textarea, select, [role=combobox], [role=listbox]",
        )
      )
        return;
      closePanel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [closePanel, state.slot]);

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
        search={
          <ShelfSearch
            onChoose={(slot) =>
              openSection(slot.code.split(".")[0] ?? null, slot.code)
            }
          />
        }
      />
      <ShelfSummary totals={data.totals} />
      {undo ? (
        <div className={styles.statusLine} role="status">
          <span>
            Исключено {undo.codes.length} {pluralPlaces(undo.codes.length)}:{" "}
            {undo.codes.join(", ")}
          </span>
          <TextButton
            disabled={restoreMany.isPending}
            onClick={() => {
              setUndoError(null);
              void restoreMany
                .mutateAsync(undo.slotIds)
                .then(({ failed, firstError }) => {
                  if (failed.length === 0) {
                    setUndo(null);
                    return;
                  }
                  const remaining = new Set(failed);
                  setUndo({
                    slotIds: undo.slotIds.filter((id) => remaining.has(id)),
                    codes: undo.codes.filter((_, index) =>
                      remaining.has(undo.slotIds[index]!),
                    ),
                  });
                  setUndoError(shelfErrorMessage(firstError));
                });
            }}
          >
            Отменить
          </TextButton>
          <TextButton
            onClick={() => {
              setUndo(null);
              setUndoError(null);
            }}
          >
            Скрыть
          </TextButton>
          {undoError ? (
            <span role="alert" className={styles.undoError}>
              Не удалось вернуть: {undoError}
            </span>
          ) : null}
        </div>
      ) : null}
      <div
        className={styles.layout}
        data-panel={selectedSlotId && !selectionMode ? "open" : "closed"}
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
              canCurate={capabilities.canCurate}
              selectionMode={selectionMode}
              selectedIds={new Set(selected.keys())}
              onSelectionModeChange={(on) =>
                on ? setSelectionMode(true) : resetSelection()
              }
              onSelect={(slot) => {
                if (!selectionMode) {
                  selectSlot(slot.code);
                  return;
                }
                setSelected((current) => {
                  const next = new Map(current);
                  if (next.has(slot.id)) next.delete(slot.id);
                  else if (next.size < BULK_EXCLUDE_MAX_ITEMS)
                    next.set(slot.id, {
                      code: slot.code,
                      version: slot.version,
                    });
                  return next;
                });
              }}
            />
          ) : null}
          {selectionMode && bulkForm ? (
            <div className={styles.panel}>
              <ShelfExclusionForm
                codes={[...selected.values()].map((item) => item.code)}
                hasLinkedDocuments={false}
                submitting={bulkExclude.isPending}
                serverError={bulkError}
                onCancel={() => setBulkForm(false)}
                onSubmit={(input) => {
                  setBulkError(null);
                  const slotIds = [...selected.keys()];
                  const codes = [...selected.values()].map((item) => item.code);
                  const items = [...selected].map(([slot_id, item]) => ({
                    slot_id,
                    version: item.version,
                  }));
                  bulkExclude.mutateAsync({ items, ...input }).then(
                    () => {
                      resetSelection();
                      setUndo({ codes, slotIds });
                    },
                    (cause: unknown) => setBulkError(shelfErrorMessage(cause)),
                  );
                }}
              />
            </div>
          ) : null}
          {selectionMode ? (
            <div
              className={styles.selectionBar}
              role="region"
              aria-label="Выбранные места"
            >
              <span>
                Выбрано {selected.size} {pluralPlaces(selected.size)}
                {selected.size >= BULK_EXCLUDE_MAX_ITEMS
                  ? ` (не больше ${BULK_EXCLUDE_MAX_ITEMS} за раз)`
                  : ""}
              </span>
              <Button
                variant="danger"
                size="sm"
                disabled={selected.size === 0}
                onClick={() => setBulkForm(true)}
              >
                Исключить выбранные
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSelected(new Map())}
              >
                Снять выбор
              </Button>
            </div>
          ) : null}
        </div>
        {selectedSlotId && !selectionMode ? (
          <ShelfPlacePanel
            key={selectedSlotId}
            slotId={selectedSlotId}
            onClose={closePanel}
            onExcluded={(codes, slotIds) => setUndo({ codes, slotIds })}
          />
        ) : null}
      </div>
    </div>
  );
}
