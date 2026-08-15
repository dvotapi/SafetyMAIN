import type { Meta, StoryObj } from "@storybook/react";
import { useMemo, useState } from "react";
import { createColumnHelper } from "@tanstack/react-table";

import { Button } from "@/components/primitives/Button";
import {
  DataTable,
  type DataTableColumnDef,
} from "@/components/data-display/DataTable";

type HazardRow = {
  id: string;
  title: string;
  status: string;
  owner: string;
};

const columnHelper = createColumnHelper<HazardRow>();

const sampleData: HazardRow[] = [
  { id: "1", title: "Slip hazard", status: "Active", owner: "Alex" },
  { id: "2", title: "Chemical exposure", status: "Draft", owner: "Sam" },
  {
    id: "3",
    title: "Forklift traffic",
    status: "Under Review",
    owner: "Jordan",
  },
  { id: "4", title: "Noise levels", status: "Active", owner: "Alex" },
  { id: "5", title: "Confined space", status: "Archived", owner: "Taylor" },
];

const meta: Meta<typeof DataTable<HazardRow>> = {
  title: "Data Display/DataTable",
  component: DataTable,
};

export default meta;
type Story = StoryObj<typeof DataTable<HazardRow>>;

export const Default: Story = {
  render: function DefaultTableStory() {
    const columns = useMemo(
      () =>
        [
          columnHelper.accessor("title", {
            header: "Title",
            cell: (info) => info.getValue(),
            enableSorting: true,
          }),
          columnHelper.accessor("status", {
            header: "Status",
            cell: (info) => info.getValue(),
            enableSorting: true,
          }),
          columnHelper.accessor("owner", {
            header: "Owner",
            cell: (info) => info.getValue(),
          }),
        ] as DataTableColumnDef<HazardRow>[],
      [],
    );

    return (
      <DataTable
        data={sampleData}
        columns={columns}
        enableRowSelection
        bulkActions={<Button size="sm">Export</Button>}
        pageSize={3}
      />
    );
  },
};

export const Loading: Story = {
  render: function LoadingTableStory() {
    const columns = useMemo(
      () =>
        [
          columnHelper.accessor("title", { header: "Title" }),
          columnHelper.accessor("status", { header: "Status" }),
        ] as DataTableColumnDef<HazardRow>[],
      [],
    );
    return <DataTable data={[]} columns={columns} loading pageSize={5} />;
  },
};

export const WithGlobalFilter: Story = {
  render: function FilteredTableStory() {
    const [filter, setFilter] = useState("");
    const columns = useMemo(
      () =>
        [
          columnHelper.accessor("title", {
            header: "Title",
            enableSorting: true,
          }),
          columnHelper.accessor("owner", { header: "Owner" }),
        ] as DataTableColumnDef<HazardRow>[],
      [],
    );
    return (
      <div style={{ display: "grid", gap: 12 }}>
        <input
          aria-label="Filter table"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter…"
        />
        <DataTable
          data={sampleData}
          columns={columns}
          globalFilter={filter}
          onGlobalFilterChange={setFilter}
        />
      </div>
    );
  },
};
