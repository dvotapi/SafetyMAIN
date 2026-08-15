import { type ReactNode } from "react";

import { Alert, type AlertTone } from "@/components/feedback/Feedback";
import { Card } from "@/components/primitives/Surface";
import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface AlertCardProps {
  tone?: AlertTone;
  title?: string;
  children: ReactNode;
  className?: string;
}

export function AlertCard({
  tone = "warning",
  title,
  children,
  className,
}: AlertCardProps) {
  return (
    <Card className={cx(styles.alertCard, className)}>
      <Alert tone={tone} {...(title ? { title } : {})}>
        {children}
      </Alert>
    </Card>
  );
}
