import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface TrendPlaceholderProps {
  label?: string;
  className?: string;
}

export function TrendPlaceholder({
  label = "Trend chart placeholder",
  className,
}: TrendPlaceholderProps) {
  return (
    <div className={cx(styles.placeholder, className)} aria-hidden>
      {label}
    </div>
  );
}
