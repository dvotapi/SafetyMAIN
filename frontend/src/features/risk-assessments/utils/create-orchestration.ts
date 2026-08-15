import {
  formValuesToCreateRequest,
  formValuesToUpdateRequest,
} from "@/features/risk-assessments/mappers/risk-assessment-mappers";
import type { RiskAssessmentFormValues } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type {
  CreateRiskAssessmentDto,
  RiskAssessment,
  UpdateRiskAssessmentDto,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { shouldPatchRiskInputsAfterCreate } from "@/features/risk-assessments/utils/create-workflow";

export type CreateOrchestrationDeps = {
  create: (body: CreateRiskAssessmentDto) => Promise<RiskAssessment>;
  update: (
    id: string,
    body: UpdateRiskAssessmentDto,
  ) => Promise<RiskAssessment>;
};

export type CreateOrchestrationResult =
  | {
      status: "created";
      assessment: RiskAssessment;
      patched: false;
    }
  | {
      status: "created";
      assessment: RiskAssessment;
      patched: true;
    }
  | {
      status: "partial_failure";
      assessment: RiskAssessment;
      patchError: unknown;
    }
  | {
      status: "create_failed";
      error: unknown;
    };

export type PatchRetryResult =
  | { status: "updated"; assessment: RiskAssessment }
  | { status: "failed"; error: unknown };

/**
 * Two-step create: POST draft, then optional PATCH for risk inputs.
 * Never rolls back the draft on PATCH failure.
 */
export async function orchestrateRiskAssessmentCreate(
  values: RiskAssessmentFormValues,
  deps: CreateOrchestrationDeps,
): Promise<CreateOrchestrationResult> {
  let created: RiskAssessment;
  try {
    created = await deps.create(formValuesToCreateRequest(values));
  } catch (error) {
    return { status: "create_failed", error };
  }

  if (!shouldPatchRiskInputsAfterCreate(values)) {
    return { status: "created", assessment: created, patched: false };
  }

  try {
    const updated = await deps.update(
      created.id,
      formValuesToUpdateRequest(values, created.version, {
        includeRiskInputs: true,
      }),
    );
    return { status: "created", assessment: updated, patched: true };
  } catch (patchError) {
    return {
      status: "partial_failure",
      assessment: created,
      patchError,
    };
  }
}

/**
 * PATCH-only retry after partial failure. Never creates a new assessment.
 */
export async function orchestrateRiskAssessmentPatchRetry(
  values: RiskAssessmentFormValues,
  assessmentId: string,
  expectedVersion: number,
  deps: Pick<CreateOrchestrationDeps, "update">,
): Promise<PatchRetryResult> {
  try {
    const updated = await deps.update(
      assessmentId,
      formValuesToUpdateRequest(values, expectedVersion, {
        includeRiskInputs: true,
      }),
    );
    return { status: "updated", assessment: updated };
  } catch (error) {
    return { status: "failed", error };
  }
}
