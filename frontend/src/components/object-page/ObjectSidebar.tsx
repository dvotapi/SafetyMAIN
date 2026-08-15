import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectSidebarProps {
  children: ReactNode;
  className?: string;
}

export function ObjectSidebar({ children, className }: ObjectSidebarProps) {
  return (
    <aside
      className={cx(styles.sidebar, className)}
      aria-label="Object details"
    >
      {children}
    </aside>
  );
}
