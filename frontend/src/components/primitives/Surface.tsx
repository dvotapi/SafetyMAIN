import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Surface.module.css";

export function Card({
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={cx(styles.card, className)} {...rest}>
      {children}
    </div>
  );
}

export function Panel({
  className,
  children,
  heading,
  actions,
  ...rest
}: HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  heading?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className={cx(styles.panel, className)} {...rest}>
      {heading || actions ? (
        <div className={styles.panelHeader}>
          <div>{heading}</div>
          {actions}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function Divider({ className, ...rest }: HTMLAttributes<HTMLHRElement>) {
  return <hr className={cx(styles.divider, className)} {...rest} />;
}
