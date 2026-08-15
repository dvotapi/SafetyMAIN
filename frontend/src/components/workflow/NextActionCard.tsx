import { type ReactNode } from "react";

import { Card } from "@/components/primitives/Surface";
import { Heading, Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Workflow.module.css";

export interface NextActionCardProps {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function NextActionCard({
  title,
  description,
  actions,
  className,
}: NextActionCardProps) {
  return (
    <Card className={cx(styles.nextAction, className)}>
      <Heading level={3}>{title}</Heading>
      {description ? (
        <Text tone="muted" variant="caption">
          {description}
        </Text>
      ) : null}
      {actions}
    </Card>
  );
}
