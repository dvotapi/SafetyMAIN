import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Activity.module.css";

export interface TimestampProps {
  children: ReactNode;
  dateTime?: string;
  className?: string;
}

export function Timestamp({ children, dateTime, className }: TimestampProps) {
  return (
    <time
      className={cx(styles.timestamp, className)}
      {...(dateTime ? { dateTime } : {})}
    >
      {children}
    </time>
  );
}
