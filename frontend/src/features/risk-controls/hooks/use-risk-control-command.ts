"use client";

import { useState } from "react";

import { useToast } from "@/components";
import { riskControlConflictVariantFromCode } from "@/features/risk-controls/components/risk-control-conflict-dialog";
import type { RiskControlLifecycleAction } from "@/features/risk-controls/types/risk-control-types";
import {
  ConflictError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

export type { RiskControlConflictVariant } from "@/features/risk-controls/components/risk-control-conflict-dialog";

function readLocation(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map(String);
  }
  return [];
}

function readViolationMessage(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

/**
 * Flattens FastAPI-style `{ violations: [{ location, message }] }` details
 * into `"<last location segment>: <message>"` lines. Falls back to the
 * generic user-safe message when the shape does not match.
 */
function flattenValidationError(error: ValidationError): string {
  const details = error.details;
  if (details && typeof details === "object" && !Array.isArray(details)) {
    const violations = (details as Record<string, unknown>)["violations"];
    if (Array.isArray(violations) && violations.length > 0) {
      const lines = violations
        .map((item) => {
          if (!item || typeof item !== "object") {
            return null;
          }
          const violation = item as Record<string, unknown>;
          const location = readLocation(
            violation["location"] ?? violation["loc"],
          );
          const last = location.length > 0 ? location[location.length - 1] : null;
          const message =
            readViolationMessage(violation["message"]) ??
            readViolationMessage(violation["msg"]);
          if (!last || !message) {
            return null;
          }
          return `${last}: ${message}`;
        })
        .filter((line): line is string => Boolean(line));
      if (lines.length > 0) {
        return lines.join("; ");
      }
    }
  }
  return toUserSafeMessage(error);
}

export function useRiskControlCommand() {
  const { toast } = useToast();
  const [busyAction, setBusyAction] =
    useState<RiskControlLifecycleAction | null>(null);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [conflictVariant, setConflictVariant] = useState<
    "version_conflict" | "duplicate_materialization"
  >("version_conflict");

  async function runCommand<T>(
    action: RiskControlLifecycleAction,
    runner: () => Promise<T>,
    successTitle: string,
    successDescription?: string,
  ): Promise<boolean> {
    setCommandError(null);
    setBusyAction(action);
    try {
      await runner();
      toast({
        tone: "success",
        title: successTitle,
        ...(successDescription ? { description: successDescription } : {}),
      });
      return true;
    } catch (error) {
      if (error instanceof ConflictError) {
        setConflictVariant(riskControlConflictVariantFromCode(error.code));
        setConflictOpen(true);
        // Conflicts never retry automatically — surfaced only via the dialog.
      } else if (error instanceof ValidationError) {
        setCommandError(flattenValidationError(error));
      } else {
        setCommandError(toUserSafeMessage(error));
      }
      return false;
    } finally {
      setBusyAction(null);
    }
  }

  return {
    runCommand,
    busyAction,
    commandError,
    conflictOpen,
    setConflictOpen,
    conflictVariant,
  };
}
