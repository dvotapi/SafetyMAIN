import { type ReactNode } from "react";

import { Alert } from "@/components/feedback/Feedback";
import { cx } from "@/utils/cx";

import styles from "./Forms.module.css";

export interface ReviewModeProps {
  children: ReactNode;
  message?: string;
  className?: string;
}

export function ReviewMode({
  children,
  message = "Режим проверки — поля доступны только для чтения",
  className,
}: ReviewModeProps) {
  return (
    <div className={cx(styles.reviewMode, className)} aria-readonly="true">
      <Alert tone="info" title="Проверка" className={styles.reviewModeBanner}>
        {message}
      </Alert>
      {children}
    </div>
  );
}
