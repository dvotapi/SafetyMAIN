import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";

import { FilterBar } from "@/components/filters/FilterBar";
import { QuickFilter } from "@/components/filters/QuickFilter";
import { Search } from "@/components/filters/Search";
import { FilterChip } from "@/components/filters/FilterChip";
import { ClearAll } from "@/components/filters/ClearAll";
import { AdvancedFilter } from "@/components/filters/AdvancedFilter";
import { DateRangeFilter } from "@/components/filters/DateRangeFilter";

const meta: Meta<typeof FilterBar> = {
  title: "Filters/FilterBar",
  component: FilterBar,
};

export default meta;
type Story = StoryObj<typeof FilterBar>;

export const Default: Story = {
  render: function FilterBarDemo() {
    const [query, setQuery] = useState("");
    const [active, setActive] = useState("all");
    return (
      <div style={{ display: "grid", gap: 12 }}>
        <FilterBar>
          <Search
            value={query}
            onChange={setQuery}
            onClear={() => setQuery("")}
          />
          <QuickFilter
            active={active === "all"}
            onClick={() => setActive("all")}
          >
            All
          </QuickFilter>
          <QuickFilter
            active={active === "mine"}
            count={4}
            onClick={() => setActive("mine")}
          >
            Mine
          </QuickFilter>
          <FilterChip
            label="Status"
            value="Active"
            onRemove={() => undefined}
          />
          <ClearAll />
        </FilterBar>
        <AdvancedFilter>
          <DateRangeFilter />
        </AdvancedFilter>
      </div>
    );
  },
};
