"use client";

import type { ReactNode } from "react";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { ShelfOverviewDto } from "@/features/document-shelf/types/shelf-dto";
import {
  pluralPlaces,
  pluralSections,
} from "@/features/document-shelf/utils/shelf-labels";
import type { ShelfFilter } from "@/features/document-shelf/utils/shelf-url-state";
import { formatDateOnly } from "@/utils/format-date";

const FILTERS: ReadonlyArray<{ value: ShelfFilter; label: string }> = [
  { value: "all", label: "Все места" },
  { value: "problems", label: "Проблемные" },
  { value: "mandatory", label: "Обязательные" },
];

export function ShelfHeader({
  overview,
  filter,
  excludedHidden,
  onFilterChange,
  onExcludedHiddenChange,
  search,
}: {
  overview: ShelfOverviewDto;
  filter: ShelfFilter;
  excludedHidden: boolean;
  onFilterChange: (filter: ShelfFilter) => void;
  onExcludedHiddenChange: (hidden: boolean) => void;
  search?: ReactNode;
}) {
  const places = overview.totals.places;
  const sections = overview.sections.length;
  return (
    <header className={styles.header}>
      <div>
        <h1 className={styles.title}>Полка документов</h1>
        <p className={styles.subline}>
          {places} {pluralPlaces(places)} в {sections}{" "}
          {pluralSections(sections)}
          {" · исключено "}
          {overview.totals.excluded}
          {overview.last_imported_at
            ? ` · реестр сверен с НПА ${formatDateOnly(overview.last_imported_at)}`
            : ""}
        </p>
      </div>
      <div className={styles.controls}>
        {search}
        <div className={styles.controls} role="group" aria-label="Фильтр мест">
          {FILTERS.map((item) => (
            <button
              key={item.value}
              type="button"
              className={styles.chip}
              aria-pressed={filter === item.value}
              onClick={() => onFilterChange(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          className={styles.chip}
          aria-pressed={!excludedHidden}
          onClick={() => onExcludedHiddenChange(!excludedHidden)}
        >
          {excludedHidden ? "Исключённые скрыты" : "Исключённые видны"}
        </button>
      </div>
    </header>
  );
}
