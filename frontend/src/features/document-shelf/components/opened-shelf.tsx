"use client";

import clsx from "clsx";

import { Alert, Button, Skeleton } from "@/components";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import { ShelfSpine } from "@/features/document-shelf/components/shelf-spine";
import type {
  ShelfSectionSlotsDto,
  ShelfSectionSummaryDto,
  ShelfSlotSummaryDto,
} from "@/features/document-shelf/types/shelf-dto";
import { slotMatches } from "@/features/document-shelf/utils/shelf-filters";
import { GROUP_LABELS } from "@/features/document-shelf/utils/shelf-labels";
import type { ShelfFilter } from "@/features/document-shelf/utils/shelf-url-state";

const LEGEND = [
  "present",
  "in_progress",
  "review",
  "missing",
  "to_clarify",
  "excluded",
] as const;

export function OpenedShelf({
  summary,
  data,
  loading,
  error,
  onRetry,
  selectedSlot,
  filter,
  excludedHidden,
  onSelect,
}: {
  summary: ShelfSectionSummaryDto;
  data: ShelfSectionSlotsDto | undefined;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  selectedSlot: string | null;
  filter: ShelfFilter;
  excludedHidden: boolean;
  onSelect: (slot: ShelfSlotSummaryDto) => void;
}) {
  return (
    <section
      id="shelf-opened"
      className={styles.card}
      aria-labelledby="shelf-opened-title"
    >
      <div className={styles.shelfHeader}>
        <div>
          <span className={clsx(styles.mono, styles.ink)}>
            {String(summary.number).padStart(2, "0")}
          </span>{" "}
          <h2 id="shelf-opened-title" style={{ display: "inline", margin: 0 }}>
            {summary.title}
          </h2>
        </div>
        <span className={styles.ink}>
          {summary.by_group.present} из {summary.total} в порядке ·{" "}
          {summary.mandatory_total} обязательных · исключено{" "}
          {summary.by_group.excluded}
        </span>
      </div>
      <ul className={styles.legend} aria-label="Обозначения">
        {LEGEND.map((group) => (
          <li key={group} className={styles.count}>
            <span
              aria-hidden="true"
              className={clsx(
                styles.swatch,
                styles[group],
                group === "in_progress" && styles.ribbon,
              )}
            />
            {GROUP_LABELS[group]}
          </li>
        ))}
      </ul>
      {error ? (
        <Alert tone="danger" title="Не удалось загрузить полку">
          {error}{" "}
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Повторить
          </Button>
        </Alert>
      ) : loading || !data ? (
        <div
          className={styles.subshelves}
          aria-busy="true"
          aria-label="Загрузка полки"
        >
          {[0, 1, 2].map((index) => (
            <Skeleton key={index} height="170px" />
          ))}
        </div>
      ) : (
        <div className={styles.subshelves}>
          {data.subsections.map((subsection) => {
            const slots = subsection.slots.filter(
              (slot) => !(excludedHidden && slot.group === "excluded"),
            );
            return (
              <div key={subsection.code} className={styles.subshelf}>
                <div className={styles.subshelfTitle}>
                  <span className={styles.mono}>
                    {subsection.code.split(".")[1]}
                  </span>{" "}
                  {subsection.title}
                </div>
                <div className={styles.spines}>
                  {slots.map((slot) => (
                    <ShelfSpine
                      key={slot.id}
                      slot={slot}
                      subsectionTitle={subsection.title}
                      selected={slot.code === selectedSlot}
                      dimmed={!slotMatches(slot, filter)}
                      onSelect={onSelect}
                    />
                  ))}
                </div>
                <div className={styles.plank} aria-hidden="true" />
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
