import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface TrendPlaceholderProps {
  label?: string;
  className?: string;
}

export function TrendPlaceholder({
  label = "Заглушка графика динамики",
  className,
}: TrendPlaceholderProps) {
  return (
    <div className={cx(styles.placeholder, className)} aria-hidden>
      {label}
    </div>
  );
}
