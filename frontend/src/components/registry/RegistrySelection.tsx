import { type ReactNode } from "react";

import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export interface RegistrySelectionProps {
  count: number;
  actions?: ReactNode;
  className?: string;
}

export function RegistrySelection({
  count,
  actions,
  className,
}: RegistrySelectionProps) {
  if (count <= 0) return null;
  return (
    <div className={cx(styles.selectionBar, className)} role="status">
      <Text variant="label">{count} selected</Text>
      {actions}
    </div>
  );
}
