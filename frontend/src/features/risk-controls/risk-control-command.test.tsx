import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Label, TextArea } from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";

afterEach(() => {
  cleanup();
});

/** Mirrors how a reason-only command (archive/cancel/suspend/supersede)
 * will use the generic shell: a single required TextArea child, validated
 * locally before the caller's onConfirm ever runs. */
function ReasonCommandHost({
  onConfirmed,
  errorMessage = null,
}: {
  onConfirmed: (reason: string) => void;
  errorMessage?: string | null;
}) {
  const [open, setOpen] = useState(true);
  const [reason, setReason] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  return (
    <RiskControlCommandDialog
      open={open}
      onOpenChange={setOpen}
      title="Suspend control"
      version={4}
      errorMessage={validationError ?? errorMessage}
      confirmLabel="Suspend control"
      onConfirm={() => {
        if (!reason.trim()) {
          setValidationError("Reason is required");
          return;
        }
        setValidationError(null);
        onConfirmed(reason.trim());
      }}
    >
      <div style={{ display: "grid", gap: 8 }}>
        <Label htmlFor="suspend-reason" required>
          Reason
        </Label>
        <TextArea
          id="suspend-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </div>
    </RiskControlCommandDialog>
  );
}

describe("RiskControlCommandDialog", () => {
  it("states the required version in the description", () => {
    render(
      <RiskControlCommandDialog
        open
        onOpenChange={() => {}}
        title="Suspend control"
        version={7}
        onConfirm={() => {}}
      />,
    );

    expect(
      screen.getByText("This action uses version 7."),
    ).toBeInTheDocument();
  });

  it("does not fire confirm when a required reason is left blank", async () => {
    const user = userEvent.setup();
    const onConfirmed = vi.fn();

    render(<ReasonCommandHost onConfirmed={onConfirmed} />);

    await user.click(
      screen.getByRole("button", { name: "Suspend control" }),
    );

    expect(onConfirmed).not.toHaveBeenCalled();
    expect(screen.getByText("Reason is required")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/Reason/i), "No longer needed");
    await user.click(
      screen.getByRole("button", { name: "Suspend control" }),
    );

    await waitFor(() => {
      expect(onConfirmed).toHaveBeenCalledWith("No longer needed");
    });
  });

  it("renders the danger alert when an error message is set", () => {
    render(
      <RiskControlCommandDialog
        open
        onOpenChange={() => {}}
        title="Suspend control"
        version={2}
        errorMessage="location: Reason must be at least 3 characters"
        onConfirm={() => {}}
      />,
    );

    expect(
      screen.getByText("location: Reason must be at least 3 characters"),
    ).toBeInTheDocument();
  });

  it("moves focus inside the dialog when it opens", async () => {
    render(
      <RiskControlCommandDialog
        open
        onOpenChange={() => {}}
        title="Suspend control"
        version={2}
        onConfirm={() => {}}
      >
        <p>Body content</p>
      </RiskControlCommandDialog>,
    );

    const dialog = await screen.findByRole("dialog");
    await waitFor(() => {
      expect(dialog).toContainElement(document.activeElement as HTMLElement);
    });
  });
});
