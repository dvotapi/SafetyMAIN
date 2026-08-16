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
import {
  useAddRiskControlEvidenceMutation,
  useAssignRiskControlOwnerMutation,
  useCompleteRiskControlImplementationMutation,
  usePlanRiskControlMutation,
  useRecordRiskControlVerificationMutation,
  useStartRiskControlImplementationMutation,
  useUpdateRiskControlProgressMutation,
} from "@/features/risk-controls/api/risk-control-mutations";
import {
  useRiskControlActivityQuery,
  useRiskControlAssessmentQuery,
  useRiskControlDetailQuery,
  useRiskControlHazardQuery,
} from "@/features/risk-controls/api/risk-control-queries";
import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
import { EffectivenessSummary } from "@/features/risk-controls/components/effectiveness-summary";
import { EvidenceList } from "@/features/risk-controls/components/evidence-list";
import { ImplementationPlanSection } from "@/features/risk-controls/components/implementation-plan-section";
import { ImplementationProgressSection } from "@/features/risk-controls/components/implementation-progress-section";
import { ImplementationSummary } from "@/features/risk-controls/components/implementation-summary";
import { RiskControlActivity } from "@/features/risk-controls/components/risk-control-activity";
import { RiskControlConflictDialog } from "@/features/risk-controls/components/risk-control-conflict-dialog";
import { RiskControlRelationships } from "@/features/risk-controls/components/risk-control-relationships";
import {
  RiskControlProperties,
  RiskControlSummary,
} from "@/features/risk-controls/components/risk-control-summary";
import { SourceSnapshot } from "@/features/risk-controls/components/source-snapshot";
import { VerificationForm } from "@/features/risk-controls/components/verification-form";
import { VerificationHistory } from "@/features/risk-controls/components/verification-history";
import { useRiskControlCommand } from "@/features/risk-controls/hooks/use-risk-control-command";
import { mapRiskControlCapabilities } from "@/features/risk-controls/hooks/use-risk-control-permissions";
import { latestVerification } from "@/features/risk-controls/mappers/risk-control-mappers";
import { evidenceFormValuesToRequest } from "@/features/risk-controls/schemas/evidence-schema";
import {
  completeImplementationFormValuesToRequest,
  progressFormValuesToRequest,
} from "@/features/risk-controls/schemas/implementation-progress-schema";
import { planFormValuesToRequest } from "@/features/risk-controls/schemas/implementation-schema";
import { ownerFormValuesToRequest } from "@/features/risk-controls/schemas/owner-schema";
import { verificationFormValuesToRequest } from "@/features/risk-controls/schemas/verification-schema";
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
  const [planDialogOpen, setPlanDialogOpen] = useState(false);
  const [startDialogOpen, setStartDialogOpen] = useState(false);
  const [progressDialogOpen, setProgressDialogOpen] = useState(false);
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false);
  const [evidenceDialogOpen, setEvidenceDialogOpen] = useState(false);
  const [verificationDialogOpen, setVerificationDialogOpen] = useState(false);

  const assignOwnerMutation = useAssignRiskControlOwnerMutation(riskControlId);
  const addEvidenceMutation = useAddRiskControlEvidenceMutation(riskControlId);
  const planMutation = usePlanRiskControlMutation(riskControlId);
  const startImplementationMutation =
    useStartRiskControlImplementationMutation(riskControlId);
  const updateProgressMutation =
    useUpdateRiskControlProgressMutation(riskControlId);
  const completeImplementationMutation =
    useCompleteRiskControlImplementationMutation(riskControlId);
  const recordVerificationMutation =
    useRecordRiskControlVerificationMutation(riskControlId);
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
        <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
          <ImplementationPlanSection
            status={control.status}
            ownerAssigned={control.owner !== null}
            version={control.version}
            verificationMethodRequirement={control.verificationMethodRequirement}
            capabilities={capabilities}
            open={planDialogOpen}
            onOpenChange={setPlanDialogOpen}
            loading={busyAction === "plan"}
            errorMessage={commandError}
            onPlan={async (values) => {
              const succeeded = await runCommand(
                "plan",
                () =>
                  planMutation.mutateAsync(
                    planFormValuesToRequest(values, control.version),
                  ),
                "Implementation planned",
              );
              if (succeeded) {
                setPlanDialogOpen(false);
              }
            }}
          />
          <ImplementationProgressSection
            control={control}
            capabilities={capabilities}
            startOpen={startDialogOpen}
            onStartOpenChange={setStartDialogOpen}
            progressOpen={progressDialogOpen}
            onProgressOpenChange={setProgressDialogOpen}
            completeOpen={completeDialogOpen}
            onCompleteOpenChange={setCompleteDialogOpen}
            startLoading={busyAction === "start_implementation"}
            progressLoading={busyAction === "update_progress"}
            completeLoading={busyAction === "complete_implementation"}
            errorMessage={commandError}
            onStart={async () => {
              await runCommand(
                "start_implementation",
                () =>
                  startImplementationMutation.mutateAsync({
                    expected_version: control.version,
                  }),
                "Implementation started",
              );
            }}
            onProgress={async (values) => {
              const succeeded = await runCommand(
                "update_progress",
                () =>
                  updateProgressMutation.mutateAsync(
                    progressFormValuesToRequest(values, control.version),
                  ),
                "Progress updated",
              );
              if (succeeded) {
                setProgressDialogOpen(false);
              }
            }}
            onComplete={async (values) => {
              const succeeded = await runCommand(
                "complete_implementation",
                () =>
                  completeImplementationMutation.mutateAsync(
                    completeImplementationFormValuesToRequest(
                      values,
                      control.version,
                      control.evidence.length === 0,
                    ),
                  ),
                "Implementation completed",
              );
              if (succeeded) {
                setCompleteDialogOpen(false);
              }
            }}
          />
          <ImplementationSummary
            implementation={control.implementation}
            status={control}
          />
        </div>
      ) : null}

      {tab === "evidence" ? (
        <EvidenceList
          evidence={control.evidence}
          status={control.status}
          version={control.version}
          capabilities={capabilities}
          open={evidenceDialogOpen}
          onOpenChange={setEvidenceDialogOpen}
          loading={busyAction === "add_evidence"}
          errorMessage={commandError}
          onAdd={async (values) => {
            const succeeded = await runCommand(
              "add_evidence",
              () =>
                addEvidenceMutation.mutateAsync(
                  evidenceFormValuesToRequest(values, control.version),
                ),
              "Evidence added",
            );
            if (succeeded) {
              setEvidenceDialogOpen(false);
            }
          }}
        />
      ) : null}

      {tab === "verification" ? (
        <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
          <EffectivenessSummary
            latestResult={control.latestEffectivenessResult}
            latestVerification={latest}
            riskAssessmentId={control.riskAssessmentId}
          />
          <VerificationForm
            status={control.status}
            capabilities={capabilities}
            reviewRequired={control.reviewSchedule.reviewRequired}
            noReviewReason={control.reviewSchedule.noReviewReason}
            hasExistingEvidence={control.evidence.length > 0}
            version={control.version}
            open={verificationDialogOpen}
            onOpenChange={setVerificationDialogOpen}
            loading={busyAction === "verify"}
            errorMessage={commandError}
            onSubmit={async (values) => {
              const successDescription =
                values.result === "partially_effective"
                  ? "Effectiveness is now Verified Partially Effective. The control's lifecycle status is unchanged."
                  : undefined;
              const succeeded = await runCommand(
                "verify",
                () =>
                  recordVerificationMutation.mutateAsync(
                    verificationFormValuesToRequest(values, control.version),
                  ),
                "Verification recorded",
                successDescription,
              );
              if (succeeded) {
                setVerificationDialogOpen(false);
              }
            }}
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
