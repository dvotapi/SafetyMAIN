import { z } from "zod";

import type {
  AffectedSubjectDto,
  HazardCategoryDto,
  HazardSourceDto,
  SafetyDirectionDto,
} from "@/features/hazards/types/hazard-types";

export const HAZARD_CATEGORIES = [
  "physical",
  "mechanical",
  "electrical",
  "chemical",
  "biological",
  "ergonomic",
  "psychosocial",
  "fire_and_explosion",
  "thermal",
  "radiation",
  "pressure",
  "work_at_height",
  "confined_space",
  "transport",
  "environmental",
  "dangerous_goods",
  "process_safety",
  "natural_hazard",
  "organizational",
  "other",
] as const satisfies readonly HazardCategoryDto[];

export const SAFETY_DIRECTIONS = [
  "occupational_safety",
  "industrial_safety",
  "fire_safety",
  "environmental_safety",
  "transport_safety",
  "dangerous_goods_transport",
  "civil_defense_and_emergency",
  "sanitary_and_hygienic_safety",
  "electrical_safety",
  "radiation_safety",
] as const satisfies readonly SafetyDirectionDto[];

export const HAZARD_SOURCES = [
  "employee_report",
  "inspection",
  "incident_investigation",
  "near_miss",
  "risk_assessment",
  "regulatory_assessment",
  "audit",
  "management_review",
  "change_management",
  "equipment_documentation",
  "sout",
  "production_control",
  "environmental_monitoring",
  "transport_control",
  "other",
] as const satisfies readonly HazardSourceDto[];

export const AFFECTED_SUBJECTS = [
  "employee",
  "contractor",
  "visitor",
  "driver",
  "passenger",
  "public",
  "environment",
  "equipment",
  "building",
  "transport_vehicle",
  "cargo",
  "production_process",
] as const satisfies readonly AffectedSubjectDto[];

export const hazardFormSchema = z.object({
  code: z.string().trim().min(1, "Code is required").max(64),
  title: z.string().trim().min(1, "Title is required").max(512),
  description: z.string().max(10_000),
  category: z.enum(HAZARD_CATEGORIES),
  safetyDirections: z
    .array(z.enum(SAFETY_DIRECTIONS))
    .min(1, "Select at least one safety direction"),
  source: z.enum(HAZARD_SOURCES),
  affectedSubjects: z.array(z.enum(AFFECTED_SUBJECTS)),
  locationReference: z.string().max(512),
  processReference: z.string().max(512),
  equipmentReference: z.string().max(512),
});

export type HazardFormValues = z.infer<typeof hazardFormSchema>;

export const defaultHazardFormValues: HazardFormValues = {
  code: "",
  title: "",
  description: "",
  category: "physical",
  safetyDirections: ["occupational_safety"],
  source: "inspection",
  affectedSubjects: [],
  locationReference: "",
  processReference: "",
  equipmentReference: "",
};
