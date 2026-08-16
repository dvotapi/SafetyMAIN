import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { WorkflowStepper } from "@/components/workflow/WorkflowStepper";

afterEach(() => {
  cleanup();
});

describe("WorkflowStepper", () => {
  it("marks current step and completed steps", () => {
    render(
      <WorkflowStepper
        steps={[
          { id: "a", label: "Draft" },
          { id: "b", label: "Review" },
          { id: "c", label: "Done" },
        ]}
        currentStepId="b"
        completedStepIds={["a"]}
      />,
    );

    expect(screen.getByText("Review").closest("li")).toHaveAttribute(
      "aria-current",
      "step",
    );
    expect(screen.getByLabelText("Ход процесса")).toBeInTheDocument();
  });
});
