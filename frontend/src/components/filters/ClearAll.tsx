"use client";

import { Button } from "@/components/primitives/Button";
import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface ClearAllProps {
  onClick?: () => void;
  disabled?: boolean;
  label?: string;
  className?: string;
}

export function ClearAll({
  onClick,
  disabled = false,
  label = "Clear all",
  className,
}: ClearAllProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className={cx(styles.clearAll, className)}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </Button>
  );
}
