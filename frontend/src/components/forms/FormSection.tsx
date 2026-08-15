import { type HTMLAttributes, type ReactNode } from "react";

import { Heading, Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Forms.module.css";

export interface FormSectionProps extends Omit<
  HTMLAttributes<HTMLElement>,
  "title"
> {
  title?: ReactNode;
  description?: ReactNode;
  children: ReactNode;
}

export function FormSection({
  title,
  description,
  children,
  className,
  ...rest
}: FormSectionProps) {
  return (
    <section className={cx(styles.section, className)} {...rest}>
      {title || description ? (
        <div className={styles.sectionHeader}>
          {title ? <Heading level={3}>{title}</Heading> : null}
          {description ? (
            <Text tone="muted" variant="caption">
              {description}
            </Text>
          ) : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
