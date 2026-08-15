import { type ReactNode } from "react";

import { Panel } from "@/components/primitives/Surface";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectRelationship {
  id: string;
  label: ReactNode;
  value: ReactNode;
}

export interface ObjectRelationshipsProps {
  items: ObjectRelationship[];
  heading?: ReactNode;
  className?: string;
}

export function ObjectRelationships({
  items,
  heading = "Relationships",
  className,
}: ObjectRelationshipsProps) {
  return (
    <Panel heading={heading} className={cx(styles.relationships, className)}>
      {items.map((item) => (
        <div key={item.id} className={styles.relationshipItem}>
          <Text variant="label">{item.label}</Text>
          <Text as="span" variant="caption">
            {item.value}
          </Text>
        </div>
      ))}
    </Panel>
  );
}
