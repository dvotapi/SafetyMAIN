"use client";

import { useEffect, useId, useState } from "react";

import { Input } from "@/components";

import { useShelfSearchQuery } from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { ShelfSlotSummaryDto } from "@/features/document-shelf/types/shelf-dto";
import { STATUS_LABELS } from "@/features/document-shelf/utils/shelf-labels";

/** Combobox over `GET /shelf/slots?q=` (ARIA 1.2 pattern, §4.3.9). */
export function ShelfSearch({
  onChoose,
}: {
  onChoose: (slot: ShelfSlotSummaryDto) => void;
}) {
  const id = useId();
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  useEffect(() => {
    const handle = window.setTimeout(() => setQuery(draft), 250);
    return () => window.clearTimeout(handle);
  }, [draft]);
  const results = useShelfSearchQuery(query);
  const items = results.data?.items ?? [];
  const expanded = open && query.trim().length >= 2;

  function choose(slot: ShelfSlotSummaryDto) {
    onChoose(slot);
    setOpen(false);
    setDraft("");
  }

  return (
    <div className={styles.search}>
      <label htmlFor={`${id}-input`} className="visually-hidden">
        Поиск по полке
      </label>
      <Input
        id={`${id}-input`}
        role="combobox"
        aria-expanded={expanded}
        aria-controls={`${id}-list`}
        aria-autocomplete="list"
        aria-activedescendant={
          expanded && items[active] ? `${id}-opt-${active}` : undefined
        }
        placeholder="Поиск: код или название"
        value={draft}
        autoComplete="off"
        onChange={(event) => {
          setDraft(event.target.value);
          setActive(0);
          setOpen(true);
        }}
        onBlur={() => window.setTimeout(() => setOpen(false), 150)}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActive((index) =>
              Math.min(index + 1, Math.max(items.length - 1, 0)),
            );
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive((index) => Math.max(index - 1, 0));
          } else if (event.key === "Enter" && expanded && items[active]) {
            event.preventDefault();
            choose(items[active]!);
          } else if (event.key === "Escape") {
            setOpen(false);
          }
        }}
      />
      {expanded ? (
        <ul
          id={`${id}-list`}
          role="listbox"
          aria-label="Найденные места"
          className={styles.searchList}
        >
          {results.isPending ? (
            <li
              className={styles.searchOption}
              role="option"
              aria-selected={false}
              aria-disabled="true"
            >
              Поиск…
            </li>
          ) : items.length === 0 ? (
            <li
              className={styles.searchOption}
              role="option"
              aria-selected={false}
              aria-disabled="true"
            >
              Ничего не найдено
            </li>
          ) : (
            items.map((slot, index) => (
              <li
                key={slot.id}
                id={`${id}-opt-${index}`}
                role="option"
                aria-selected={index === active}
                className={styles.searchOption}
                onMouseDown={(event) => {
                  event.preventDefault();
                  choose(slot);
                }}
              >
                <span className={styles.mono}>{slot.code}</span> {slot.title}
                <span className={styles.ink}>
                  {" "}
                  · {STATUS_LABELS[slot.effective_status]}
                </span>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
