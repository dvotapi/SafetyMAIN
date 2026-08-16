"use client";

import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Workflow.module.css";

export interface WorkflowStep {
  id: string;
  label: string;
}

export interface WorkflowStepperProps {
  steps: WorkflowStep[];
  currentStepId: string;
  completedStepIds?: string[];
  className?: string;
}

export function WorkflowStepper({
  steps,
  currentStepId,
  completedStepIds = [],
  className,
}: WorkflowStepperProps) {
  const completed = new Set(completedStepIds);
  return (
    <ol className={cx(styles.stepper, className)} aria-label="Ход процесса">
      {steps.map((step, index) => {
        const isComplete = completed.has(step.id);
        const isCurrent = step.id === currentStepId;
        return (
          <li
            key={step.id}
            className={cx(
              styles.step,
              isComplete && styles.stepComplete,
              isCurrent && styles.stepCurrent,
            )}
            aria-current={isCurrent ? "step" : undefined}
          >
            <span className={styles.stepMarker} aria-hidden>
              {isComplete ? (
                <Icon name="check" size="xs" decorative />
              ) : (
                index + 1
              )}
            </span>
            <span className={styles.stepLabel}>{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
