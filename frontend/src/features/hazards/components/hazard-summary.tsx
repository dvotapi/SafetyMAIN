import {
  DescriptionItem,
  DescriptionList,
  Heading,
  Panel,
  PropertyGrid,
  StatusBadge,
  Text,
} from "@/components";

import type { Hazard } from "@/features/hazards/types/hazard-types";
import {
  formatHazardEnumLabel,
  hazardStatusToVisual,
} from "@/features/hazards/utils/hazard-status";

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function HazardSummary({ hazard }: { hazard: Hazard }) {
  return (
    <Panel>
      <PropertyGrid columns={2}>
        <div>
          <Text variant="caption" tone="muted">
            Reference
          </Text>
          <Text>{hazard.code}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Status
          </Text>
          <StatusBadge status={hazardStatusToVisual(hazard.status)} />
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Category
          </Text>
          <Text>{formatHazardEnumLabel(hazard.category)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Location
          </Text>
          <Text>{hazard.locationReference ?? "—"}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Updated
          </Text>
          <Text>{formatDate(hazard.updatedAt)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Version
          </Text>
          <Text>{hazard.version}</Text>
        </div>
      </PropertyGrid>
    </Panel>
  );
}

export function HazardProperties({ hazard }: { hazard: Hazard }) {
  return (
    <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
      <Panel>
        <Heading level={2}>Hazard details</Heading>
        <DescriptionList>
          <DescriptionItem term="Title" details={hazard.title} />
          <DescriptionItem
            term="Description"
            details={hazard.description || "—"}
          />
          <DescriptionItem
            term="Category"
            details={formatHazardEnumLabel(hazard.category)}
          />
          <DescriptionItem
            term="Source"
            details={formatHazardEnumLabel(hazard.source)}
          />
          <DescriptionItem
            term="Safety directions"
            details={
              hazard.safetyDirections.map(formatHazardEnumLabel).join(", ") ||
              "—"
            }
          />
          <DescriptionItem
            term="Affected subjects"
            details={
              hazard.affectedSubjects.map(formatHazardEnumLabel).join(", ") ||
              "—"
            }
          />
        </DescriptionList>
      </Panel>
      <Panel>
        <Heading level={2}>Location and scope</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Location"
            details={hazard.locationReference ?? "—"}
          />
          <DescriptionItem
            term="Process"
            details={hazard.processReference ?? "—"}
          />
          <DescriptionItem
            term="Equipment"
            details={hazard.equipmentReference ?? "—"}
          />
        </DescriptionList>
      </Panel>
      <Panel>
        <Heading level={2}>Lifecycle</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Status"
            details={
              <StatusBadge status={hazardStatusToVisual(hazard.status)} />
            }
          />
          <DescriptionItem
            term="Identified"
            details={formatDate(hazard.identifiedAt)}
          />
          <DescriptionItem
            term="Reviewed"
            details={formatDate(hazard.reviewedAt)}
          />
          <DescriptionItem
            term="Archived"
            details={formatDate(hazard.archivedAt)}
          />
          <DescriptionItem
            term="Created"
            details={formatDate(hazard.createdAt)}
          />
          <DescriptionItem
            term="Updated"
            details={formatDate(hazard.updatedAt)}
          />
        </DescriptionList>
      </Panel>
    </div>
  );
}
