"use client";

import clsx from "clsx";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type {
  ShelfEffectiveStatus,
  ShelfStatusGroup,
} from "@/features/document-shelf/types/shelf-dto";
import { STATUS_LABELS } from "@/features/document-shelf/utils/shelf-labels";

/** Same shape language as the spines: swatch pattern + text. */
export function ShelfStatusBadge({
  group,
  status,
}: {
  group: ShelfStatusGroup;
  status: ShelfEffectiveStatus;
}) {
  return (
    <span className={styles.badge}>
      <span
        aria-hidden="true"
        className={clsx(
          styles.swatch,
          styles[group],
          group === "in_progress" && styles.ribbon,
        )}
      />
      {STATUS_LABELS[status]}
    </span>
  );
}
