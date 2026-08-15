import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { Timeline } from "@/components/timeline/Timeline";

afterEach(() => {
  cleanup();
});

describe("Timeline", () => {
  it("groups events by date and toggles collapse", async () => {
    const user = userEvent.setup();
    render(
      <Timeline
        events={[
          {
            id: "1",
            title: "Today event",
            timestamp: new Date("2026-07-25T10:00:00"),
          },
          {
            id: "2",
            title: "Yesterday event",
            timestamp: new Date("2026-07-24T10:00:00"),
          },
        ]}
      />,
    );

    expect(screen.getByText("Today event")).toBeInTheDocument();
    expect(screen.getByText("Yesterday event")).toBeInTheDocument();

    const collapseButtons = screen.getAllByRole("button", { name: "Collapse" });
    await user.click(collapseButtons[0]!);

    expect(
      screen.getAllByRole("button", { name: "Expand" }).length,
    ).toBeGreaterThan(0);
  });
});
