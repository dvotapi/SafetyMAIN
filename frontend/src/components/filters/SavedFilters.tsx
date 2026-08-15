import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface SavedFiltersProps {
  className?: string;
}

/** Placeholder for saved filter presets — wired by features later. */
export function SavedFilters({ className }: SavedFiltersProps) {
  return (
    <Text
      as="span"
      variant="caption"
      tone="muted"
      className={cx(styles.savedFilters, className)}
    >
      Saved filters (coming soon)
    </Text>
  );
}
