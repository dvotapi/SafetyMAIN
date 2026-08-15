import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Navigation.module.css";

export function TopNavigation({
  brand,
  start,
  end,
  className,
}: {
  brand?: ReactNode;
  start?: ReactNode;
  end?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cx(styles.topNav, className)}>
      <div className={styles.topStart}>
        {brand}
        {start}
      </div>
      <div className={styles.topEnd}>{end}</div>
    </header>
  );
}

export function SideNavigation({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <nav className={cx(styles.sideNav, className)}>{children}</nav>;
}

export function NavigationSection({
  title,
  children,
  className,
}: {
  title?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.navSection, className)}>
      {title ? <div className={styles.navSectionTitle}>{title}</div> : null}
      {children}
    </div>
  );
}

export { NavigationItem } from "@/components/navigation/NavigationItem";
