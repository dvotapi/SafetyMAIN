"use client";

import clsx from "clsx";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { ShelfSectionSummaryDto } from "@/features/document-shelf/types/shelf-dto";
import { GROUP_LABELS } from "@/features/document-shelf/utils/shelf-labels";
import { stripItemMatches } from "@/features/document-shelf/utils/shelf-filters";
import type { ShelfFilter } from "@/features/document-shelf/utils/shelf-url-state";

export function ShelfOverview({
  sections,
  openSection,
  filter,
  excludedHidden,
  onToggle,
}: {
  sections: ShelfSectionSummaryDto[];
  openSection: string | null;
  filter: ShelfFilter;
  excludedHidden: boolean;
  onToggle: (code: string) => void;
}) {
  return (
    <section aria-labelledby="shelf-overview-title">
      <h2 id="shelf-overview-title">Все разделы</h2>
      <ul className={styles.overview}>
        {sections.map((section) => {
          const expanded = section.code === openSection;
          return (
            <li key={section.code}>
              <button
                type="button"
                className={styles.row}
                aria-expanded={expanded}
                aria-controls={expanded ? "shelf-opened" : undefined}
                onClick={() => onToggle(section.code)}
              >
                <span className={clsx(styles.mono, styles.ink)}>
                  {String(section.number).padStart(2, "0")}
                </span>
                <span>{section.title}</span>
                <span className={styles.strip} aria-hidden="true">
                  {section.strip
                    .filter(
                      (item) => !(excludedHidden && item.group === "excluded"),
                    )
                    .map((item) => (
                      <span
                        key={item.code}
                        title={`${item.code} · ${GROUP_LABELS[item.group]}`}
                        className={clsx(
                          styles.stripBar,
                          styles[item.group],
                          !stripItemMatches(item.group, filter) &&
                            styles.dimmed,
                        )}
                      />
                    ))}
                </span>
                <span
                  className={clsx(styles.mono, styles.ink, styles.rowCounts)}
                >
                  {section.by_group.present} из {section.total}
                </span>
                <span className={styles.mono}>
                  {section.readiness_percent}%
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
