import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Forms.module.css";

export interface ValidationSummaryProps {
  title?: string;
  errors: string[];
  className?: string;
}

export function ValidationSummary({
  title = "Исправьте следующие ошибки",
  errors,
  className,
}: ValidationSummaryProps) {
  if (errors.length === 0) return null;
  return (
    <div
      className={cx(styles.validationSummary, className)}
      role="alert"
      aria-live="polite"
    >
      <Text variant="label">{title}</Text>
      <ul className={styles.validationList}>
        {errors.map((error) => (
          <li key={error}>{error}</li>
        ))}
      </ul>
    </div>
  );
}
