import { FilterBar } from "@/components/filters/FilterBar";
import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export interface RegistryFiltersProps {
  children: React.ReactNode;
  className?: string;
}

export function RegistryFilters({ children, className }: RegistryFiltersProps) {
  return (
    <FilterBar className={cx(styles.toolbarSection, className)}>
      {children}
    </FilterBar>
  );
}
