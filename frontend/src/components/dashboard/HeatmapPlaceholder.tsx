import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface HeatmapPlaceholderProps {
  label?: string;
  className?: string;
}

export function HeatmapPlaceholder({
  label = "Заглушка тепловой карты",
  className,
}: HeatmapPlaceholderProps) {
  return (
    <div className={cx(styles.placeholder, className)} aria-hidden>
      {label}
    </div>
  );
}
