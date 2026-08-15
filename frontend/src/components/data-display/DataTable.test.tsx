import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useMemo } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import { afterEach, describe, expect, it } from "vitest";

import {
  DataTable,
  type DataTableColumnDef,
} from "@/components/data-display/DataTable";

type Row = { id: string; name: string; score: number };

const rows: Row[] = [
  { id: "1", name: "Bravo", score: 20 },
  { id: "2", name: "Alpha", score: 10 },
  { id: "3", name: "Charlie", score: 30 },
];

const columnHelper = createColumnHelper<Row>();

function SortTestTable() {
  const columns = useMemo(
    () =>
      [
        columnHelper.accessor("name", {
          header: "Name",
          enableSorting: true,
        }),
        columnHelper.accessor("score", {
          header: "Score",
          enableSorting: true,
        }),
      ] as DataTableColumnDef<Row>[],
    [],
  );

  return (
    <DataTable
      data={rows}
      columns={columns}
      getRowId={(row) => row.id}
      pageSize={10}
    />
  );
}

function SelectionTestTable() {
  const columns = useMemo(
    () =>
      [
        columnHelper.accessor("name", {
          header: "Name",
          enableSorting: true,
        }),
        columnHelper.accessor("score", {
          header: "Score",
          enableSorting: true,
        }),
      ] as DataTableColumnDef<Row>[],
    [],
  );

  return (
    <DataTable
      data={rows}
      columns={columns}
      enableRowSelection
      getRowId={(row) => row.id}
      pageSize={10}
    />
  );
}

afterEach(() => {
  cleanup();
});

describe("DataTable", () => {
  it("sorts rows when header is clicked", async () => {
    const user = userEvent.setup();
    render(<SortTestTable />);

    const nameHeader = screen.getByRole("columnheader", { name: /Name/i });
    await user.click(nameHeader.querySelector("button")!);

    const nameCells = screen
      .getAllByRole("cell")
      .filter((cell) => /Alpha|Bravo|Charlie/.test(cell.textContent ?? ""));
    expect(nameCells[0]).toHaveTextContent("Alpha");
  });

  it("selects individual rows", async () => {
    const user = userEvent.setup();
    render(<SelectionTestTable />);

    const checkboxes = screen.getAllByRole("checkbox");
    const firstRow = checkboxes[1];
    expect(firstRow).toBeDefined();
    await user.click(firstRow!);

    expect(firstRow).toBeChecked();
  });
});
