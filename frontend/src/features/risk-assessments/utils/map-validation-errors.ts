import type { Path } from "react-hook-form";

import type { RiskAssessmentFormValues } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";

export type MappedFieldError = {
  name: Path<RiskAssessmentFormValues>;
  message: string;
};

export type MappedValidationErrors = {
  fieldErrors: MappedFieldError[];
  rootMessage: string | null;
};

const DIRECT_FIELD_MAP: Record<string, Path<RiskAssessmentFormValues>> = {
  hazard_id: "hazardId",
  code: "code",
  title: "title",
  assessment_profile: "assessmentProfile",
  assessment_date: "assessmentDate",
  assessed_object_type: "assessedObjectType",
  assessed_object_reference: "assessedObjectReference",
  "assessed_object.object_type": "assessedObjectType",
  "assessed_object.reference": "assessedObjectReference",
  review_due_date: "reviewDueDate",
  "review_schedule.review_due_date": "reviewDueDate",
  review_frequency_days: "reviewFrequencyDays",
  "review_schedule.review_frequency_days": "reviewFrequencyDays",
  review_reason: "reviewReason",
  "review_schedule.review_reason": "reviewReason",
  triggered_by: "reviewTriggeredBy",
  "review_schedule.triggered_by": "reviewTriggeredBy",
  competency_requirements: "competencyRequirements",
  acceptance_decision: "acceptanceDecision",
  "acceptance.decision": "acceptanceDecision",
  acceptance_justification: "acceptanceJustification",
  "acceptance.justification": "acceptanceJustification",
  acceptance_reviewer_id: "acceptanceReviewerId",
  "acceptance.reviewer_id": "acceptanceReviewerId",
  "inherent_risk.probability": "inherentRisk.probabilityScore",
  "inherent_risk.severity": "inherentRisk.severityScore",
  "inherent_risk.explanation": "inherentRisk.explanation",
  "residual_risk.probability": "residualRisk.probabilityScore",
  "residual_risk.severity": "residualRisk.severityScore",
  "residual_risk.explanation": "residualRisk.explanation",
};

function messageFromUnknown(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (Array.isArray(value)) {
    const parts = value
      .map((item) => messageFromUnknown(item))
      .filter((item): item is string => Boolean(item));
    return parts.length > 0 ? parts.join("; ") : null;
  }
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return (
      messageFromUnknown(record["message"]) ??
      messageFromUnknown(record["msg"]) ??
      null
    );
  }
  return null;
}

function stripBodyPrefix(parts: string[]): string[] {
  const head = parts[0];
  if (head === "body" || head === "request_body") {
    return parts.slice(1);
  }
  return parts;
}

function locationToFormPath(
  location: readonly string[],
): Path<RiskAssessmentFormValues> | null {
  const parts = stripBodyPrefix([...location].map(String));
  if (parts.length === 0) {
    return null;
  }

  const joined = parts.join(".");
  const direct = DIRECT_FIELD_MAP[joined];
  if (direct) {
    return direct;
  }

  const root = parts[0];
  if (!root) {
    return null;
  }

  if (root === "assessed_object") {
    if (parts[1] === "object_type") return "assessedObjectType";
    if (parts[1] === "reference") return "assessedObjectReference";
    return "assessedObjectReference";
  }

  if (root === "inherent_risk" || root === "residual_risk") {
    const section = root === "inherent_risk" ? "inherentRisk" : "residualRisk";
    if (parts[1] === "probability") {
      return `${section}.probabilityScore` as Path<RiskAssessmentFormValues>;
    }
    if (parts[1] === "severity") {
      return `${section}.severityScore` as Path<RiskAssessmentFormValues>;
    }
    if (parts[1] === "explanation") {
      return `${section}.explanation` as Path<RiskAssessmentFormValues>;
    }
    if (parts[1] === "factors" && parts.length >= 3) {
      // factors.<index>.factor|score — map onto the evaluation section
      return section as Path<RiskAssessmentFormValues>;
    }
    return section as Path<RiskAssessmentFormValues>;
  }

  if (root === "controls") {
    if (parts.length >= 3) {
      const index = parts[1];
      const field = parts[2];
      const controlField =
        field === "control_type"
          ? "controlType"
          : field === "description"
            ? "description"
            : field === "responsible"
              ? "responsible"
              : field === "implemented"
                ? "implemented"
                : field === "effective"
                  ? "effective"
                  : null;
      if (controlField && index && /^\d+$/.test(index)) {
        return `controls.${index}.${controlField}` as Path<RiskAssessmentFormValues>;
      }
    }
    return "controls" as Path<RiskAssessmentFormValues>;
  }

  if (root === "acceptance") {
    if (parts[1] === "decision") return "acceptanceDecision";
    if (parts[1] === "justification") return "acceptanceJustification";
    if (parts[1] === "reviewer_id") return "acceptanceReviewerId";
    return "acceptanceDecision";
  }

  const mappedRoot = DIRECT_FIELD_MAP[root];
  if (mappedRoot) {
    return mappedRoot;
  }

  return null;
}

function pushFieldError(
  target: MappedFieldError[],
  name: Path<RiskAssessmentFormValues>,
  message: string,
): void {
  if (!message.trim()) {
    return;
  }
  const existing = target.find((item) => item.name === name);
  if (existing) {
    existing.message = `${existing.message}; ${message}`;
    return;
  }
  target.push({ name, message });
}

function collectFromRecord(
  record: Record<string, unknown>,
  prefix: string[],
  fieldErrors: MappedFieldError[],
  unmapped: string[],
): void {
  for (const [key, value] of Object.entries(record)) {
    if (key === "violations" && Array.isArray(value)) {
      continue;
    }
    const pathParts = [...prefix, key];
    if (value && typeof value === "object" && !Array.isArray(value)) {
      collectFromRecord(
        value as Record<string, unknown>,
        pathParts,
        fieldErrors,
        unmapped,
      );
      continue;
    }
    const message = messageFromUnknown(value);
    if (!message) {
      continue;
    }
    const formPath = locationToFormPath(pathParts);
    if (formPath) {
      pushFieldError(fieldErrors, formPath, message);
    } else {
      unmapped.push(`${pathParts.join(".")}: ${message}`);
    }
  }
}

/**
 * Maps backend validation `details` onto RHF form paths.
 * Supports:
 * - FastAPI-style `{ violations: [{ location, message }] }`
 * - Flat/nested dicts of field → message | string[]
 * Unknown paths accumulate into rootMessage.
 */
export function mapRiskAssessmentValidationDetails(
  details: unknown,
  fallbackMessage: string,
): MappedValidationErrors {
  const fieldErrors: MappedFieldError[] = [];
  const unmapped: string[] = [];

  if (details && typeof details === "object" && !Array.isArray(details)) {
    const record = details as Record<string, unknown>;
    const violations = record["violations"];
    if (Array.isArray(violations)) {
      for (const item of violations) {
        if (!item || typeof item !== "object") {
          continue;
        }
        const violation = item as Record<string, unknown>;
        const location = Array.isArray(violation["location"])
          ? violation["location"].map(String)
          : Array.isArray(violation["loc"])
            ? violation["loc"].map(String)
            : [];
        const message =
          messageFromUnknown(violation["message"]) ??
          messageFromUnknown(violation["msg"]) ??
          fallbackMessage;
        const formPath = locationToFormPath(location);
        if (formPath) {
          pushFieldError(fieldErrors, formPath, message);
        } else if (location.length > 0) {
          unmapped.push(`${location.join(".")}: ${message}`);
        } else {
          unmapped.push(message);
        }
      }
    }

    collectFromRecord(record, [], fieldErrors, unmapped);
  } else {
    const message = messageFromUnknown(details);
    if (message) {
      unmapped.push(message);
    }
  }

  const rootParts = [...unmapped];
  if (fieldErrors.length === 0 && rootParts.length === 0) {
    rootParts.push(fallbackMessage);
  }

  return {
    fieldErrors,
    rootMessage: rootParts.length > 0 ? rootParts.join("; ") : null,
  };
}
