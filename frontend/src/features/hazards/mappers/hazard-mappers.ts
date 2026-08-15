import type {
  CreateHazardDto,
  Hazard,
  HazardDto,
  HazardListDto,
  HazardListResult,
  UpdateHazardDto,
} from "@/features/hazards/types/hazard-types";
import type { HazardFormValues } from "@/features/hazards/schemas/hazard-form-schema";

function emptyToNull(value: string | undefined | null): string | null {
  if (value === undefined || value === null) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length === 0 ? null : trimmed;
}

export function mapHazardDto(dto: HazardDto): Hazard {
  return {
    id: dto.id,
    organizationId: dto.organization_id,
    code: dto.code,
    title: dto.title,
    description: dto.description,
    category: dto.category,
    safetyDirections: dto.safety_directions,
    source: dto.source,
    affectedSubjects: dto.affected_subjects,
    locationReference: dto.location_reference,
    processReference: dto.process_reference,
    equipmentReference: dto.equipment_reference,
    extensionReferences: dto.extension_references,
    status: dto.status,
    identifiedAt: dto.identified_at,
    identifiedBy: dto.identified_by,
    reviewedAt: dto.reviewed_at,
    reviewedBy: dto.reviewed_by,
    archivedAt: dto.archived_at,
    archivedBy: dto.archived_by,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
    version: dto.version,
  };
}

export function mapHazardListDto(dto: HazardListDto): HazardListResult {
  return {
    items: dto.items.map(mapHazardDto),
    pagination: dto.pagination,
  };
}

export function formValuesToCreateRequest(
  values: HazardFormValues,
): CreateHazardDto {
  const body: CreateHazardDto = {
    code: values.code.trim(),
    title: values.title.trim(),
    category: values.category,
    safety_directions: values.safetyDirections,
    source: values.source,
  };
  const description = values.description.trim();
  if (description) {
    body.description = description;
  }
  if (values.affectedSubjects.length > 0) {
    body.affected_subjects = values.affectedSubjects;
  }
  const location = emptyToNull(values.locationReference);
  if (location !== null) {
    body.location_reference = location;
  }
  const process = emptyToNull(values.processReference);
  if (process !== null) {
    body.process_reference = process;
  }
  const equipment = emptyToNull(values.equipmentReference);
  if (equipment !== null) {
    body.equipment_reference = equipment;
  }
  return body;
}

export function hazardToFormValues(hazard: Hazard): HazardFormValues {
  return {
    code: hazard.code,
    title: hazard.title,
    description: hazard.description,
    category: hazard.category,
    safetyDirections: hazard.safetyDirections,
    source: hazard.source,
    affectedSubjects: hazard.affectedSubjects,
    locationReference: hazard.locationReference ?? "",
    processReference: hazard.processReference ?? "",
    equipmentReference: hazard.equipmentReference ?? "",
  };
}

export function formValuesToUpdateRequest(
  values: HazardFormValues,
  expectedVersion: number,
  options?: { includeSource?: boolean },
): UpdateHazardDto {
  const body: UpdateHazardDto = {
    expected_version: expectedVersion,
    title: values.title.trim(),
    description: values.description.trim(),
    category: values.category,
    safety_directions: values.safetyDirections,
    affected_subjects: values.affectedSubjects,
    location_reference: emptyToNull(values.locationReference),
    process_reference: emptyToNull(values.processReference),
    equipment_reference: emptyToNull(values.equipmentReference),
  };
  if (options?.includeSource) {
    body.source = values.source;
  }
  return body;
}
