"use client";

import clsx from "clsx";
import { useId, useState } from "react";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { ShelfSlotSummaryDto } from "@/features/document-shelf/types/shelf-dto";
import {
  OBLIGATION_LABELS,
  STATUS_LABELS,
} from "@/features/document-shelf/utils/shelf-labels";
import { spineSize } from "@/features/document-shelf/utils/spine-geometry";

export function ShelfSpine({
  slot,
  subsectionTitle,
  selected,
  dimmed,
  onSelect,
  selectionMode = false,
  checked = false,
}: {
  slot: ShelfSlotSummaryDto;
  subsectionTitle: string;
  selected: boolean;
  dimmed: boolean;
  onSelect: (slot: ShelfSlotSummaryDto) => void;
  /** Bulk selection: a click toggles the checkbox instead of opening the panel. */
  selectionMode?: boolean;
  checked?: boolean;
}) {
  const [tipOpen, setTipOpen] = useState(false);
  const tipId = useId();
  const excluded = slot.group === "excluded";
  const size = spineSize(slot.document_kind, slot.obligation_level, excluded);
  const status = STATUS_LABELS[slot.effective_status];
  const selectable = selectionMode && !excluded;
  return (
    <div className={clsx(styles.spineWrap, dimmed && styles.dimmed)}>
      {slot.has_acknowledgement_gap ? (
        <span className={styles.ackDot} aria-hidden="true" />
      ) : null}
      <button
        type="button"
        className={clsx(
          styles.spine,
          styles[slot.group],
          slot.group === "in_progress" && styles.ribbon,
        )}
        style={{ width: size.width, height: size.height }}
        aria-label={`${slot.code} ${slot.title}. ${status}`}
        aria-describedby={tipOpen ? tipId : undefined}
        aria-current={!selectionMode && selected ? "true" : undefined}
        aria-pressed={selectable ? checked : undefined}
        disabled={selectionMode && excluded}
        data-code={slot.code}
        onClick={() => onSelect(slot)}
        onMouseEnter={() => setTipOpen(true)}
        onMouseLeave={() => setTipOpen(false)}
        onFocus={() => setTipOpen(true)}
        onBlur={() => setTipOpen(false)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setTipOpen(false);
        }}
      >
        {excluded ? null : (
          <span className={styles.spineLabel} aria-hidden="true">
            {slot.short_title}
          </span>
        )}
        {selectable ? (
          <span
            className={styles.spineCheck}
            data-checked={checked}
            aria-hidden="true"
          />
        ) : null}
      </button>
      {selected && !selectionMode ? (
        <span className={styles.caret} aria-hidden="true" />
      ) : null}
      {tipOpen ? (
        <div id={tipId} role="tooltip" className={styles.tooltip}>
          <p className={styles.mono}>{slot.code}</p>
          <p>{slot.title}</p>
          <p>
            {subsectionTitle} · {slot.document_kind} ·{" "}
            {OBLIGATION_LABELS[slot.obligation_level] ?? slot.obligation_level}
          </p>
          <p>{status}</p>
        </div>
      ) : null}
    </div>
  );
}
