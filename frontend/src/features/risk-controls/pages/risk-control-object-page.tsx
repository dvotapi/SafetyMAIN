"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
  ObjectHeader,
  ObjectTabs,
  StatusBadge,
  Text,
} from "@/components";
import { PageContainer } from "@/components/patterns/Page";
import { useAssignRiskControlOwnerMutation } from "@/features/risk-controls/api/risk-control-mutations";
import {
  useRiskControlActivityQuery,
  useRiskControlAssessmentQuery,
  useRiskControlDetailQuery,
  useRiskControlHazardQuery,
} from "@/features/risk-controls/api/risk-control-queries";
import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
import { EffectivenessSummary } from "@/features/risk-controls/components/effectiveness-summary";
import { EvidenceList } from "@/features/risk-controls/components/evidence-list";
import { ImplementationSummary } from "@/features/risk-controls/components/implementation-summary";
import { RiskControlActivity } from "@/features/risk-controls/components/risk-control-activity";
import { RiskControlConflictDialog } from "@/features/risk-controls/components/risk-control-conflict-dialog";
import { RiskControlRelationships } from "@/features/risk-controls/components/risk-control-relationships";
import {
  RiskControlProperties,
  RiskControlSummary,
} from "@/features/risk-controls/components/risk-control-summary";
import { SourceSnapshot } from "@/features/risk-controls/components/source-snapshot";
import { VerificationHistory } from "@/features/risk-controls/components/verification-history";
import { useRiskControlCommand } from "@/features/risk-controls/hooks/use-risk-control-command";
import { mapRiskControlCapabilities } from "@/features/risk-controls/hooks/use-risk-control-permissions";
import { latestVerification } from "@/features/risk-controls/mappers/risk-control-mappers";
import { ownerFormValuesToRequest } from "@/features/risk-controls/schemas/owner-schema";
import {
  effectivenessLabel,
  effectivenessToVisual,
  implementationStateLabel,
  riskControlStatusLabel,
  riskControlStatusToVisual,
} from "@/features/risk-controls/utils/risk-control-status";
import { useAuth } from "@/hooks/auth";
import {
  NotFoundError,
  PermissionError,
  toUserSafeMessage,
} from "@/services/api/errors";

export function RiskControlObjectPage({
  riskControlId,
}: {
  riskControlId: string;
}) {
  const { hasPermission } = useAuth();
  const capabilities = mapRiskControlCapabilities(hasPermission);
  const detail = useRiskControlDetailQuery(riskControlId, capabilities.canRead);
  const control = detail.data;

  const hazard = useRiskControlHazardQuery(
    control?.hazardId ?? "",
    Boolean(control?.hazardId) && capabilities.canViewHazard,
  );
  const assessment = useRiskControlAssessmentQuery(
    control?.riskAssessmentId ?? "",
    Boolean(control?.riskAssessmentId) && capabilities.canViewAssessment,
  );
  const activity = useRiskControlActivityQuery(
    riskControlId,
    capabilities.canViewActivity && detail.isSuccess,
  );

  const [tab, setTab] = useState("overview");
  const [ownerDialogOpen, setOwnerDialogOpen] = useState(false);

  const assignOwnerMutation = useAssignRiskControlOwnerMutation(riskControlId);
  const {
    runCommand,
    busyAction,
    commandError,
    conflictOpen,
    setConflictOpen,
    conflictVariant,
  } = useRiskControlCommand();

  useEffect(() => {
    if (control) {
      document.title = `${control.code} · SafetyMAIN`;
    } else {
      document.title = "Risk Control · SafetyMAIN";
    }
  }, [control]);

  if (!capabilities.canRead) {
    return (
      <PageContainer variant="object">
        <EmptyState
          title="Risk control unavailable"
          description="You do not have permission to view risk controls."
        />
      </PageContainer>
    );
  }

  if (detail.isLoading) {
    return (
      <PageContainer variant="object">
        <LoadingState label="Loading risk control" />
      </PageContainer>
    );
  }

  if (detail.isError) {
    if (detail.error instanceof NotFoundError) {
      return (
        <PageContainer variant="object">
          <EmptyState
            title="Risk control not found"
            description="This control does not exist or is not available in the active organization."
            action={
              <Button asChild variant="secondary">
                <Link href="/safety/risk-controls">Back to registry</Link>
              </Button>
            }
          />
        </PageContainer>
      );
    }
    if (detail.error instanceof PermissionError) {
      return (
        <PageContainer variant="object">
          <EmptyState
            title="Access denied"
            description={toUserSafeMessage(detail.error)}
          />
        </PageContainer>
      );
    }
    return (
      <PageContainer variant="object">
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Unable to load risk control">
            {toUserSafeMessage(detail.error)}
          </Alert>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void detail.refetch()}
          >
            Retry
          </Button>
        </div>
      </PageContainer>
    );
  }

  if (!control) {
    return null;
  }

  const latest = latestVerification(control);
  const effectivenessVisual = effectivenessToVisual(
    control.latestEffectivenessResult,
  );
  const effectivenessBadgeLabel = effectivenessLabel(
    control.latestEffectivenessResult,
  );

  const showRelationshipsTab = Boolean(
    control.hazardId || control.riskAssessmentId,
  );
  const showActivityTab = capabilities.canViewActivity;

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "implementation", label: "Implementation" },
    { id: "evidence", label: "Evidence" },
    { id: "verification", label: "Verification" },
    ...(showRelationshipsTab
      ? [{ id: "relationships", label: "Relationships" }]
      : []),
    ...(showActivityTab ? [{ id: "activity", label: "Activity" }] : []),
  ];

  return (
    <PageContainer variant="object">
      <ObjectHeader
        title={control.title}
        subtitle={control.code}
        status={
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              flexWrap: "wrap",
            }}
          >
            <StatusBadge
              status={riskControlStatusToVisual(control.status)}
              label={riskControlStatusLabel(control.status)}
            />
            <Text variant="caption" tone="muted">
              {implementationStateLabel({
                status: control.status,
                progress: control.implementation.progress,
                actualCompletionDate:
                  control.implementation.actualCompletionDate,
              })}
            </Text>
            {effectivenessVisual ? (
              <StatusBadge
                status={effectivenessVisual}
                label={effectivenessBadgeLabel}
              />
            ) : (
              <Text variant="caption" tone="muted">
                {effectivenessBadgeLabel}
              </Text>
            )}
            {control.isOverdue ? (
              <StatusBadge status="overdue" label="Overdue" />
            ) : null}
          </div>
        }
        meta={
          <Text tone="muted" variant="caption">
            Version {control.version}
          </Text>
        }
        actions={
          <Button asChild variant="ghost">
            <Link href="/safety/risk-controls">Back to registry</Link>
          </Button>
        }
      />

      <RiskControlSummary control={control} />

      <ObjectTabs tabs={tabs} activeTabId={tab} onTabChange={setTab} />

      {tab === "overview" ? (
        <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
          <ControlOwnerSection
            owner={control.owner}
            status={control.status}
            version={control.version}
            capabilities={capabilities}
            open={ownerDialogOpen}
            onOpenChange={setOwnerDialogOpen}
            loading={busyAction === "assign_owner"}
            errorMessage={commandError}
            onAssign={async (values) => {
              const succeeded = await runCommand(
                "assign_owner",
                () =>
                  assignOwnerMutation.mutateAsync(
                    ownerFormValuesToRequest(values, control.version),
                  ),
                "Owner assigned",
              );
              if (succeeded) {
                setOwnerDialogOpen(false);
              }
            }}
          />
          <RiskControlProperties
            control={control}
            hazard={hazard.data}
            assessment={assessment.data}
          />
          <SourceSnapshot source={control.source} />
          <EffectivenessSummary
            latestResult={control.latestEffectivenessResult}
            latestVerification={latest}
            riskAssessmentId={control.riskAssessmentId}
          />
        </div>
      ) : null}

      {tab === "implementation" ? (
        <ImplementationSummary
          implementation={control.implementation}
          status={control}
        />
      ) : null}

      {tab === "evidence" ? <EvidenceList evidence={control.evidence} /> : null}

      {tab === "verification" ? (
        <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
          <EffectivenessSummary
            latestResult={control.latestEffectivenessResult}
            latestVerification={latest}
            riskAssessmentId={control.riskAssessmentId}
          />
          <VerificationHistory verifications={control.verifications} />
        </div>
      ) : null}

      {tab === "relationships" && showRelationshipsTab ? (
        <RiskControlRelationships
          control={control}
          hazard={hazard}
          assessment={assessment}
          capabilities={capabilities}
        />
      ) : null}

      {tab === "activity" && showActivityTab ? (
        <RiskControlActivity
          items={activity.data ?? []}
          loading={activity.isLoading}
          canView={capabilities.canViewActivity}
        />
      ) : null}

      <RiskControlConflictDialog
        open={conflictOpen}
        onOpenChange={setConflictOpen}
        onReload={() => void detail.refetch()}
        loading={detail.isFetching}
        variant={conflictVariant}
      />
    </PageContainer>
  );
}
