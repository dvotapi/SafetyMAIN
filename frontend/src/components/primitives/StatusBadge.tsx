import { type HTMLAttributes, type ReactNode } from "react";

import { Icon } from "@/icons/Icon";
import { statusIcons } from "@/icons/status-icons";
import { cx } from "@/utils/cx";

import styles from "./Badge.module.css";
import {
  visualStatusLabels,
  visualStatusTone,
  type VisualStatus,
} from "./status-types";

export type { StatusTone, VisualStatus } from "./status-types";
export { visualStatusLabels, visualStatusTone } from "./status-types";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
}

export function Badge({ children, className, ...rest }: BadgeProps) {
  return (
    <span className={cx(styles.badge, className)} {...rest}>
      {children}
    </span>
  );
}

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: VisualStatus;
  label?: string;
  showIcon?: boolean;
}

export function StatusBadge({
  status,
  label,
  showIcon = true,
  className,
  ...rest
}: StatusBadgeProps) {
  const text = label ?? visualStatusLabels[status];
  return (
    <span
      className={cx(styles.badge, styles.status, styles[status], className)}
      data-tone={visualStatusTone[status]}
      aria-label={`Статус: ${text}`}
      {...rest}
    >
      {showIcon ? (
        <Icon name={statusIcons[status]} size="xs" decorative />
      ) : null}
      <span>{text}</span>
    </span>
  );
}
