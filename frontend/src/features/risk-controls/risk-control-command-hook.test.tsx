import {
  act,
  cleanup,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components";
import { useRiskControlCommand } from "@/features/risk-controls/hooks/use-risk-control-command";
import {
  ConflictError,
  NotFoundError,
  PermissionError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

afterEach(() => {
  cleanup();
});

function wrapper({ children }: { children: ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>;
}

function renderCommandHook() {
  return renderHook(() => useRiskControlCommand(), { wrapper });
}

describe("useRiskControlCommand", () => {
  it("fires the success toast with the exact title/description, returns true, and clears busyAction", async () => {
    const { result } = renderCommandHook();
    const runner = vi.fn().mockResolvedValue(undefined);

    let outcome: boolean | undefined;
    await act(async () => {
      outcome = await result.current.runCommand(
        "suspend",
        runner,
        "Control suspended",
        "The control is now suspended.",
      );
    });

    expect(outcome).toBe(true);
    expect(runner).toHaveBeenCalledTimes(1);
    expect(result.current.busyAction).toBeNull();
    expect(result.current.commandError).toBeNull();
    expect(result.current.conflictOpen).toBe(false);
    expect(await screen.findByText("Control suspended")).toBeInTheDocument();
    expect(
      screen.getByText("The control is now suspended."),
    ).toBeInTheDocument();
  });

  it("sets busyAction during the call and clears it on success", async () => {
    const { result } = renderCommandHook();
    let resolveRunner: () => void = () => {};
    const runner = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveRunner = resolve;
        }),
    );

    let pending: Promise<boolean> | undefined;
    act(() => {
      pending = result.current.runCommand("resume", runner, "Control resumed");
    });

    await waitFor(() => {
      expect(result.current.busyAction).toBe("resume");
    });

    await act(async () => {
      resolveRunner();
      await pending;
    });

    expect(result.current.busyAction).toBeNull();
  });

  it("sets busyAction during the call and clears it on failure", async () => {
    const { result } = renderCommandHook();
    let rejectRunner: (error: unknown) => void = () => {};
    const runner = vi.fn(
      () =>
        new Promise<void>((_resolve, reject) => {
          rejectRunner = reject;
        }),
    );

    let pending: Promise<boolean> | undefined;
    act(() => {
      pending = result.current.runCommand(
        "suspend",
        runner,
        "Control suspended",
      );
    });

    await waitFor(() => {
      expect(result.current.busyAction).toBe("suspend");
    });

    await act(async () => {
      rejectRunner(
        new PermissionError({ message: "Not allowed", status: 403 }),
      );
      await pending;
    });

    expect(result.current.busyAction).toBeNull();
  });

  it("routes a version-conflict ConflictError to the version_conflict variant without retrying", async () => {
    const { result } = renderCommandHook();
    const conflictError = new ConflictError({
      message: "Conflict",
      status: 409,
      code: "risk_control_version_conflict",
    });
    const runner = vi.fn().mockRejectedValue(conflictError);

    let outcome: boolean | undefined;
    await act(async () => {
      outcome = await result.current.runCommand(
        "suspend",
        runner,
        "Control suspended",
      );
    });

    expect(outcome).toBe(false);
    expect(runner).toHaveBeenCalledTimes(1);
    expect(result.current.conflictOpen).toBe(true);
    expect(result.current.conflictVariant).toBe("version_conflict");
    expect(result.current.commandError).toBeNull();
  });

  it("routes a duplicate-materialization ConflictError to the duplicate_materialization variant", async () => {
    const { result } = renderCommandHook();
    const conflictError = new ConflictError({
      message: "Already materialized",
      status: 409,
      code: "risk_control_already_materialized",
    });
    const runner = vi.fn().mockRejectedValue(conflictError);

    await act(async () => {
      await result.current.runCommand("verify", runner, "Control verified");
    });

    expect(result.current.conflictOpen).toBe(true);
    expect(result.current.conflictVariant).toBe("duplicate_materialization");
  });

  it("flattens ValidationError violations into '<last segment>: <message>' lines", async () => {
    const { result } = renderCommandHook();
    const validationError = new ValidationError({
      message: "Validation failed",
      status: 422,
      details: {
        violations: [
          { location: ["body", "reason"], message: "Reason is required" },
          { loc: ["body", "notes"], msg: "Notes too long" },
        ],
      },
    });
    const runner = vi.fn().mockRejectedValue(validationError);

    await act(async () => {
      await result.current.runCommand("suspend", runner, "Control suspended");
    });

    expect(result.current.commandError).toBe(
      "reason: Reason is required; notes: Notes too long",
    );
    expect(result.current.conflictOpen).toBe(false);
  });

  it("falls back to toUserSafeMessage when ValidationError details are malformed", async () => {
    const { result } = renderCommandHook();
    const validationError = new ValidationError({
      message: "Validation failed",
      status: 422,
      details: { violations: "not-an-array" },
    });
    const runner = vi.fn().mockRejectedValue(validationError);

    await act(async () => {
      await result.current.runCommand("suspend", runner, "Control suspended");
    });

    expect(result.current.commandError).toBe(
      toUserSafeMessage(validationError),
    );
  });

  it("falls back to toUserSafeMessage when ValidationError has no details", async () => {
    const { result } = renderCommandHook();
    const validationError = new ValidationError({
      message: "Validation failed",
      status: 422,
    });
    const runner = vi.fn().mockRejectedValue(validationError);

    await act(async () => {
      await result.current.runCommand("suspend", runner, "Control suspended");
    });

    expect(result.current.commandError).toBe(
      toUserSafeMessage(validationError),
    );
  });

  it("surfaces PermissionError as toUserSafeMessage without opening the conflict dialog", async () => {
    const { result } = renderCommandHook();
    const permissionError = new PermissionError({
      message: "Not allowed",
      status: 403,
    });
    const runner = vi.fn().mockRejectedValue(permissionError);

    await act(async () => {
      await result.current.runCommand("suspend", runner, "Control suspended");
    });

    expect(result.current.commandError).toBe(
      toUserSafeMessage(permissionError),
    );
    expect(result.current.conflictOpen).toBe(false);
  });

  it("surfaces NotFoundError as toUserSafeMessage", async () => {
    const { result } = renderCommandHook();
    const notFoundError = new NotFoundError({
      message: "Not found",
      status: 404,
    });
    const runner = vi.fn().mockRejectedValue(notFoundError);

    await act(async () => {
      await result.current.runCommand("suspend", runner, "Control suspended");
    });

    expect(result.current.commandError).toBe(toUserSafeMessage(notFoundError));
  });
});
