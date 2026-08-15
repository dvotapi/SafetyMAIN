import { type ReactNode } from "react";

import {
  StatusBadge,
  type VisualStatus,
} from "@/components/primitives/StatusBadge";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Workflow.module.css";

export interface ApprovalStatusProps {
  status: VisualStatus;
  label?: string;
  approver?: ReactNode;
  className?: string;
}

export function ApprovalStatus({
  status,
  label,
  approver,
  className,
}: ApprovalStatusProps) {
  return (
    <div className={cx(styles.approvalStatus, className)}>
      <StatusBadge status={status} {...(label ? { label } : {})} />
      {approver ? (
        <Text tone="muted" variant="caption">
          {approver}
        </Text>
      ) : null}
    </div>
  );
}
