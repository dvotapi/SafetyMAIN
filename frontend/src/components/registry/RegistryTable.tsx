"use client";

import {
  DataTable,
  type DataTableProps,
} from "@/components/data-display/DataTable";
import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export type RegistryTableProps<TData> = DataTableProps<TData>;

export function RegistryTable<TData>(props: RegistryTableProps<TData>) {
  return (
    <div className={cx(styles.registry)}>
      <DataTable {...props} stickyHeader enableColumnVisibility />
    </div>
  );
}
