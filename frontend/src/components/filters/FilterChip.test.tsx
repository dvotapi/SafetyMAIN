import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FilterChip } from "@/components/filters/FilterChip";

afterEach(() => {
  cleanup();
});

describe("FilterChip", () => {
  it("renders label and value and calls onRemove", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    render(<FilterChip label="Status" value="Active" onRemove={onRemove} />);

    expect(screen.getByText("Status:")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Remove filter" }));
    expect(onRemove).toHaveBeenCalledOnce();
  });
});
