import { type ReactNode } from "react";

import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Workflow.module.css";

export interface ReviewBannerProps {
  message: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function ReviewBanner({
  message,
  actions,
  className,
}: ReviewBannerProps) {
  return (
    <div className={cx(styles.reviewBanner, className)} role="status">
      <Text variant="label">{message}</Text>
      {actions}
    </div>
  );
}
