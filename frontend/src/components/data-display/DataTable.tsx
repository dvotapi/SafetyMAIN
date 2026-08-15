"use client";

import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type ColumnDef,
  type ColumnResizeMode,
  type OnChangeFn,
  type RowSelectionState,
  type SortingState,
  type VisibilityState,
  useReactTable,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { Alert, Spinner } from "@/components/feedback/Feedback";
import { Button } from "@/components/primitives/Button";
import { Text } from "@/components/primitives/Text";
import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./DataTable.module.css";

export type DataTableDensity = "compact" | "comfortable";

export type DataTableColumnDef<TData> = ColumnDef<TData, unknown>;

export interface DataTableProps<TData> {
  data: TData[];
  columns: DataTableColumnDef<TData>[];
  density?: DataTableDensity;
  virtualize?: boolean;
  globalFilter?: string;
  onGlobalFilterChange?: (value: string) => void;
  enableRowSelection?: boolean;
  rowSelection?: RowSelectionState;
  onRowSelectionChange?: OnChangeFn<RowSelectionState>;
  bulkActions?: ReactNode;
  loading?: boolean;
  error?: ReactNode;
  emptyMessage?: string;
  pageSize?: number;
  stickyHeader?: boolean;
  enableColumnVisibility?: boolean;
  className?: string;
  getRowId?: (row: TData, index: number) => string;
}

function SortIndicator({ direction }: { direction: false | "asc" | "desc" }) {
  if (!direction) {
    return (
      <span className={styles.sortIndicator} aria-hidden>
        ↕
      </span>
    );
  }
  return (
    <Icon
      name={direction === "asc" ? "arrow-up" : "arrow-down"}
      size="xs"
      decorative
      className={styles.sortIndicator}
    />
  );
}

export function DataTable<TData>({
  data,
  columns,
  density = "comfortable",
  virtualize = false,
  globalFilter,
  onGlobalFilterChange,
  enableRowSelection = false,
  rowSelection: rowSelectionProp,
  onRowSelectionChange,
  bulkActions,
  loading = false,
  error,
  emptyMessage = "No records found",
  pageSize = 10,
  stickyHeader = true,
  enableColumnVisibility = true,
  className,
  getRowId,
}: DataTableProps<TData>) {
  const tableId = useId();
  const parentRef = useRef<HTMLDivElement>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [internalRowSelection, setInternalRowSelection] =
    useState<RowSelectionState>({});
  const [columnMenuOpen, setColumnMenuOpen] = useState(false);
  const columnResizeMode: ColumnResizeMode = "onChange";

  const rowSelection = rowSelectionProp ?? internalRowSelection;
  const handleRowSelectionChange: OnChangeFn<RowSelectionState> = useCallback(
    (updater) => {
      if (onRowSelectionChange) {
        onRowSelectionChange(updater);
      } else {
        setInternalRowSelection(updater);
      }
    },
    [onRowSelectionChange],
  );

  const selectionColumn = useMemo<DataTableColumnDef<TData>>(
    () => ({
      id: "__select",
      size: 40,
      enableSorting: false,
      enableResizing: false,
      header: ({ table }) => (
        <input
          type="checkbox"
          aria-label="Select all rows"
          checked={table.getIsAllPageRowsSelected()}
          ref={(el) => {
            if (el) {
              el.indeterminate =
                table.getIsSomePageRowsSelected() &&
                !table.getIsAllPageRowsSelected();
            }
          }}
          onChange={table.getToggleAllPageRowsSelectedHandler()}
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          aria-label={`Select row ${row.index + 1}`}
          checked={row.getIsSelected()}
          disabled={!row.getCanSelect()}
          onChange={row.getToggleSelectedHandler()}
        />
      ),
    }),
    [],
  );

  const tableColumns = useMemo(() => {
    if (!enableRowSelection) return columns;
    return [selectionColumn, ...columns];
  }, [columns, enableRowSelection, selectionColumn]);

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: {
      sorting,
      columnVisibility,
      rowSelection,
      ...(globalFilter !== undefined ? { globalFilter } : {}),
    },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: handleRowSelectionChange,
    ...(onGlobalFilterChange ? { onGlobalFilterChange } : {}),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    enableRowSelection,
    enableMultiSort: true,
    enableColumnResizing: true,
    columnResizeMode,
    initialState: { pagination: { pageSize } },
    ...(getRowId ? { getRowId } : {}),
  });

  useEffect(() => {
    table.setPageSize(pageSize);
  }, [pageSize, table]);

  const { rows } = table.getRowModel();
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => (density === "compact" ? 36 : 48),
    overscan: 8,
    enabled: virtualize && !loading && !error,
  });

  const virtualRows = virtualize ? rowVirtualizer.getVirtualItems() : null;
  const selectedCount = Object.keys(rowSelection).length;
  const paddingTop =
    virtualRows && virtualRows.length > 0 ? (virtualRows[0]?.start ?? 0) : 0;
  const paddingBottom =
    virtualRows && virtualRows.length > 0
      ? rowVirtualizer.getTotalSize() -
        (virtualRows[virtualRows.length - 1]?.end ?? 0)
      : 0;

  const renderBody = () => {
    if (loading) {
      return (
        <tbody>
          <tr>
            <td colSpan={table.getVisibleLeafColumns().length}>
              <div className={styles.state} role="status">
                <Spinner label="Loading table data" />
                <Text tone="muted" variant="caption">
                  Loading…
                </Text>
              </div>
            </td>
          </tr>
        </tbody>
      );
    }

    if (error) {
      return (
        <tbody>
          <tr>
            <td colSpan={table.getVisibleLeafColumns().length}>
              <div className={styles.state}>
                <Alert tone="danger" title="Unable to load data">
                  {error}
                </Alert>
              </div>
            </td>
          </tr>
        </tbody>
      );
    }

    if (rows.length === 0) {
      return (
        <tbody>
          <tr>
            <td colSpan={table.getVisibleLeafColumns().length}>
              <div className={styles.state}>
                <Text tone="muted">{emptyMessage}</Text>
              </div>
            </td>
          </tr>
        </tbody>
      );
    }

    const renderRow = (rowIndex: number) => {
      const row = rows[rowIndex];
      if (!row) return null;
      return (
        <tr
          key={row.id}
          className={cx(row.getIsSelected() && styles.rowSelected)}
          data-state={row.getIsSelected() ? "selected" : undefined}
        >
          {row.getVisibleCells().map((cell) => (
            <td
              key={cell.id}
              className={styles.td}
              style={{ width: cell.column.getSize() }}
            >
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </td>
          ))}
        </tr>
      );
    };

    if (virtualize && virtualRows) {
      return (
        <tbody>
          {paddingTop > 0 ? (
            <tr aria-hidden>
              <td
                colSpan={table.getVisibleLeafColumns().length}
                style={{ height: paddingTop, padding: 0, border: 0 }}
              />
            </tr>
          ) : null}
          {virtualRows.map((virtualRow) => renderRow(virtualRow.index))}
          {paddingBottom > 0 ? (
            <tr aria-hidden>
              <td
                colSpan={table.getVisibleLeafColumns().length}
                style={{ height: paddingBottom, padding: 0, border: 0 }}
              />
            </tr>
          ) : null}
        </tbody>
      );
    }

    return <tbody>{rows.map((_, index) => renderRow(index))}</tbody>;
  };

  return (
    <div className={cx(styles.tableWrap, className)} id={tableId}>
      {selectedCount > 0 && bulkActions ? (
        <div className={styles.bulkBar} role="status">
          <Text variant="label">{selectedCount} selected</Text>
          {bulkActions}
        </div>
      ) : null}

      <div className={styles.toolbar}>
        <div className={styles.toolbarGroup}>
          <Text variant="caption" tone="muted">
            {table.getFilteredRowModel().rows.length} rows
          </Text>
        </div>
        {enableColumnVisibility ? (
          <div className={styles.columnToggle}>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setColumnMenuOpen((open) => !open)}
              aria-expanded={columnMenuOpen}
              aria-haspopup="true"
            >
              Columns
            </Button>
            {columnMenuOpen ? (
              <div className={styles.columnMenu} role="menu">
                {table.getAllLeafColumns().map((column) => {
                  if (column.id === "__select") return null;
                  return (
                    <label key={column.id} className={styles.columnMenuItem}>
                      <input
                        type="checkbox"
                        checked={column.getIsVisible()}
                        onChange={column.getToggleVisibilityHandler()}
                      />
                      {typeof column.columnDef.header === "string"
                        ? column.columnDef.header
                        : column.id}
                    </label>
                  );
                })}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      <div
        ref={parentRef}
        className={cx(styles.scroll, stickyHeader && styles.stickyHeader)}
      >
        <table
          className={cx(
            styles.table,
            density === "compact"
              ? styles.densityCompact
              : styles.densityComfortable,
          )}
          style={{ width: table.getCenterTotalSize() }}
        >
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sorted = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      className={cx(
                        styles.th,
                        canSort && styles.thSortable,
                        header.column.id === "__select" && styles.checkboxCell,
                      )}
                      style={{ width: header.getSize() }}
                      aria-sort={
                        sorted === "asc"
                          ? "ascending"
                          : sorted === "desc"
                            ? "descending"
                            : canSort
                              ? "none"
                              : undefined
                      }
                    >
                      <div className={styles.thInner}>
                        {header.isPlaceholder ? null : (
                          <>
                            <button
                              type="button"
                              style={{
                                border: 0,
                                background: "transparent",
                                padding: 0,
                                font: "inherit",
                                color: "inherit",
                                cursor: canSort ? "pointer" : "default",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                              onClick={
                                canSort
                                  ? header.column.getToggleSortingHandler()
                                  : undefined
                              }
                              disabled={!canSort}
                            >
                              {flexRender(
                                header.column.columnDef.header,
                                header.getContext(),
                              )}
                              {canSort ? (
                                <SortIndicator direction={sorted} />
                              ) : null}
                            </button>
                            {header.column.getCanResize() ? (
                              <button
                                type="button"
                                className={styles.resizeHandle}
                                onMouseDown={header.getResizeHandler()}
                                onTouchStart={header.getResizeHandler()}
                                aria-label={`Resize ${header.column.id} column`}
                              />
                            ) : null}
                          </>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          {renderBody()}
        </table>
      </div>

      {!virtualize && !loading && !error && rows.length > 0 ? (
        <div className={styles.footer}>
          <div className={styles.pageInfo}>
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
          </div>
          <div className={styles.toolbarGroup}>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
