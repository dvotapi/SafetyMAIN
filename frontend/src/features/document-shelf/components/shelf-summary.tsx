"use client";

import clsx from "clsx";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { ShelfOverviewDto } from "@/features/document-shelf/types/shelf-dto";
import {
  GROUP_LABELS,
  SUMMARY_GROUPS,
} from "@/features/document-shelf/utils/shelf-labels";

export function ShelfSummary({
  totals,
}: {
  totals: ShelfOverviewDto["totals"];
}) {
  return (
    <section className={clsx(styles.card, styles.summary)} aria-label="Сводка">
      <div className={styles.readiness}>
        <span className={styles.ink}>Готовность</span>
        <span className={styles.readinessValue}>
          {totals.readiness_percent}%
        </span>
        <div
          className={styles.bar}
          role="progressbar"
          aria-label="Готовность полки"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={totals.readiness_percent}
        >
          <div
            className={styles.barFill}
            style={{ width: `${totals.readiness_percent}%` }}
          />
        </div>
      </div>
      <ul className={styles.counts}>
        {SUMMARY_GROUPS.map((group) => (
          <li key={group} className={styles.count}>
            <span
              aria-hidden="true"
              className={clsx(
                styles.swatch,
                styles[group],
                group === "in_progress" && styles.ribbon,
              )}
            />
            <span>{GROUP_LABELS[group]}</span>
            <span className={styles.mono}>{totals.by_group[group]}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
