import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface DescriptionListProps extends HTMLAttributes<HTMLDListElement> {
  children: ReactNode;
}

export function DescriptionList({
  children,
  className,
  ...rest
}: DescriptionListProps) {
  return (
    <dl className={cx(styles.descriptionList, className)} {...rest}>
      {children}
    </dl>
  );
}

export interface DescriptionItemProps {
  term: ReactNode;
  details: ReactNode;
  className?: string;
}

export function DescriptionItem({
  term,
  details,
  className,
}: DescriptionItemProps) {
  return (
    <div className={cx(styles.descriptionItem, className)}>
      <dt className={styles.descriptionTerm}>{term}</dt>
      <dd className={styles.descriptionDetails}>{details}</dd>
    </div>
  );
}
