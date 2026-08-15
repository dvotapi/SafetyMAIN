import { type ReactNode } from "react";

import { Icon } from "@/icons/Icon";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Workflow.module.css";

export interface BlockingReasonProps {
  children: ReactNode;
  className?: string;
}

export function BlockingReason({ children, className }: BlockingReasonProps) {
  return (
    <div className={cx(styles.blockingReason, className)} role="note">
      <Icon name="shield-alert" size="sm" decorative />
      <Text variant="caption">{children}</Text>
    </div>
  );
}
